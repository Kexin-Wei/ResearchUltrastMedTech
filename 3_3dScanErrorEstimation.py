""" 2022.11.22, by Kexin
Find the error of 3D scan while kidney moving compared to the one while controlling breath for kidney motion 
    - Lark Doc: https://ultrastmedtech.feishu.cn/wiki/wikcnFkhKIQjcAizJezdMf3Woqe#doxcnSaGKEcgMG0IWYNLymVnR1d
"""
from pathlib import Path
import datetime
from lib.ellipse import *

WHICH_TEST_TO_RUN = 1  # or 1, 0 = randomLocFixedProbe, 1=randomLoc3DScan


def randomLoc3DScan(totalDisplacement):
    # 1.2 随机位置3D扫描 https://ultrastmedtech.feishu.cn/wiki/wikcnFkhKIQjcAizJezdMf3Woqe#doxcnmKYcSuSq8oSWUPfGnJ2cWg
    # US scan parameters
    VY = 250  # mm/s
    SCAN_RANGE = 120  # mm
    T_total = SCAN_RANGE / VY  # s
    US_FRAME = 20  # ms
    dt = US_FRAME / 1e3  # s
    t = np.arange(0, T_total, dt)

    # Kidney Size Parameters
    KIDNEY_WIDTH = 50  # mm
    KIDNEY_LENGTH = 130  # mm

    # Kidney Motion Parameters
    # totalDisplacement = 8.48  # mm
    # totalDisplacement = 20  # mm
    # totalDisplacement = 40  # mm
    apDisplacement = 4.5  # mm
    rlDisplacement = 2.4  # mm
    # siDisplacement = np.sqrt(totalDisplacement ** 2 - apDisplacement ** 2 - rlDisplacement ** 2)  # mm

    # In plane SIRL
    sirlDisplacement = np.sqrt(totalDisplacement ** 2 - apDisplacement ** 2)  # mm
    angleSIRL = np.arcsin(apDisplacement / totalDisplacement)  # radius
    angleRL = np.arccos(rlDisplacement / sirlDisplacement)  # radius
    cosRL, sinRL = np.cos(angleRL), np.sin(angleRL)
    rotationMatrix = np.array([cosRL, -sinRL,
                               sinRL, cosRL]).reshape((2, 2))

    SIRL_KIDNEY_LENGTH = KIDNEY_LENGTH * np.cos(angleSIRL)
    SIRL_KIDNEY_WIDTH = KIDNEY_WIDTH * np.cos(angleSIRL)

    # y = A*sin(2*pi / T * t + varphi)
    A = sirlDisplacement  # mm
    T = 5  # s

    def scan_edge_t(varphi: float):
        # 1. kidney_displacement
        v_kidney_displacement = np.vectorize(kidney_displacement)
        sirl_displacement_t = v_kidney_displacement(t, A, T, varphi)
        max_index, min_index = np.argmax(sirl_displacement_t), np.argmin(sirl_displacement_t)
        xc_yc_kidney_t = np.vstack((cosRL * sirl_displacement_t, sinRL * sirl_displacement_t))

        # 2. y of the US scan
        y_us_t = SCAN_RANGE / 2 - VY * t

        # 3. kidney edge x value in US scan = intersection of line and ellipse
        # line: y=kx+c
        xy_line_t = np.vstack((np.zeros_like(y_us_t), y_us_t))
        # 3.1 in the coordinate of ellipse
        xy_line_t_in_ellipse = np.matmul(np.linalg.inv(rotationMatrix),
                                         (xy_line_t - xc_yc_kidney_t))  # see vec from ellipse
        k_line = np.tan(-angleRL)
        c_line_in_ellipse = xy_line_t_in_ellipse[1, :] - xy_line_t_in_ellipse[0, :] * k_line  # get c in y=kx+c

        # # draw in ellipse coordinate #untest
        # figt, axt = plt.subplots(figsize=(14, 5))
        # draw_ellipse(axt, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
        #              angle=0, xc=sirl_displacement_t[0], yc=0,
        #              edge_color='m')
        # draw_ellipse(axt, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
        #              angle=0, xc=sirl_displacement_t[int(len(t) / 2)], yc=0,
        #              edge_color='r', linestyle='--')
        # draw_ellipse(axt, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
        #              angle=0, xc=sirl_displacement_t[-1], yc=0,
        #              edge_color='k', linestyle='--')
        # for i in range(len(t)):
        #     x_intersect = -c_line_in_ellipse[i] / k_line
        #     draw_line(axt, min([x_intersect, 0]), max([x_intersect, 0]), c=c_line_in_ellipse[i], k=k_line)
        # axt.grid()
        # plt.show(block=False)

        # 3.2 intersection calculation
        xy_ellipse_t_in_ellipse = []
        for c in c_line_in_ellipse:
            # ellipse x at time t in ellipse
            xy_ellipse_t_in_ellipse.append(intersection_of_line_ellipse(k_line, c,
                                                                        SIRL_KIDNEY_LENGTH / 2,
                                                                        SIRL_KIDNEY_WIDTH / 2))

        xy_ellipse_t_in_ellipse = np.array(xy_ellipse_t_in_ellipse)
        xy_ellipse_t_in_ellipse = np.array([[np.vstack((xy_ellipse_t_in_ellipse[:, 0],
                                                        xy_ellipse_t_in_ellipse[:, 2]))],
                                            [np.vstack((xy_ellipse_t_in_ellipse[:, 1],
                                                        xy_ellipse_t_in_ellipse[:, 3]))]]).squeeze(axis=1)

        # 3.2 rotate back to original
        xy_ellipse_t = np.matmul(rotationMatrix, xy_ellipse_t_in_ellipse) + xc_yc_kidney_t
        return xc_yc_kidney_t, y_us_t, xy_ellipse_t, max_index, min_index

    xc_yc_kidney_t0, y_us_t0, xy_ellipse_t0, max_index0, min_index0 = scan_edge_t(
        varphi=np.random.random() * 2 * np.pi)  # [0,2*pi))
    xc_yc_kidney_t1, y_us_t1, xy_ellipse_t1, max_index1, min_index1 = scan_edge_t(
        varphi=np.random.random() * 2 * np.pi)  # [0,2*pi))
    print(max_index0, min_index0, max_index1, min_index1)
    # plot
    fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(16, 10))
    ax0, ax1, ax2 = axes[0], axes[1], axes[2]
    draw_ellipse(ax0, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
                 angle=angleRL,
                 xc=xc_yc_kidney_t0[0, max_index0], yc=xc_yc_kidney_t0[1, max_index0],
                 edge_color='r')
    draw_ellipse(ax0, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
                 angle=angleRL,
                 xc=xc_yc_kidney_t0[0, min_index0], yc=xc_yc_kidney_t0[1, min_index0],
                 edge_color='k', linestyle='--')

    draw_ellipse(ax1, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
                 angle=angleRL,
                 xc=xc_yc_kidney_t1[0, max_index1], yc=xc_yc_kidney_t1[1, max_index1],
                 edge_color='b')
    draw_ellipse(ax1, width=SIRL_KIDNEY_LENGTH, height=SIRL_KIDNEY_WIDTH,
                 angle=angleRL,
                 xc=xc_yc_kidney_t1[0, min_index1], yc=xc_yc_kidney_t1[1, min_index1],
                 edge_color='k', linestyle='--')

    for i in range(len(t)):
        draw_line(ax2, xy_ellipse_t0[0, 0, i], xy_ellipse_t0[1, 0, i], y_us_t0[i],
                  linestyle='-', color='r')  # xNeg, xPos
    for i in range(len(t)):
        draw_line(ax2, xy_ellipse_t1[0, 0, i], xy_ellipse_t1[1, 0, i], y_us_t1[i],
                  linestyle='--', color='b', linewidth=3)  # xNeg, xPos

    ax0.grid()
    ax0.axes.set_aspect('equal')
    ax0.set_xlabel("I: mm")
    ax0.set_ylabel("R: mm")
    ax0.set_title("S")
    ax0.autoscale_view()

    ax1.grid()
    ax1.axes.set_aspect('equal')
    ax1.set_xlabel("I: mm")
    ax1.set_ylabel("R: mm")
    ax1.set_title("S")
    ax1.autoscale_view()

    ax2.grid()
    ax2.axes.set_aspect('equal')
    ax2.set_xlabel("I: mm")
    ax2.set_ylabel("R: mm")
    ax2.set_title("S")

    xlims, ylims = [], []
    for ax in axes:
        ylims.append(ax.get_ylim())
        xlims.append(ax.get_xlim())
    xlim = np.abs(xlims).max()
    ylim = np.abs(ylims).max()
    for ax in axes:
        ax.set_xlim(-xlim, xlim)
        ax.set_ylim(-ylim, ylim)

    # plt.figtext(0.3, 0.5, "L")
    # plt.figtext(0.5, 0.5, "L")
    # plt.figtext(0.92, 0.5, "L")
    plt.tight_layout()
    # save
    folderPath = Path.cwd().joinpath("results").joinpath("3-kidney-3d-scan-error", "1.2")
    if not folderPath.exists():
        folderPath.mkdir()
    fig.savefig(
        folderPath.joinpath(f"Kidney Motion Error_Disp{totalDisplacement}"
                            f"_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"))  # type: ignore
    plt.show()


def randomLocFixedProbe():
    # 1.3 随机位置固定探头+3D扫描 https://ultrastmedtech.feishu.cn/wiki/wikcnFkhKIQjcAizJezdMf3Woqe#doxcnSaGKEcgMG0IWYNLymVnR1d

    # Kidney Motion Parameters
    # y = A*sin(2*pi / T * t + varphi)
    A = 40  # mm
    T = 5  # s
    VARPHI = np.random.random() * 2 * np.pi  # [0,2*pi)

    # Kidney Size Parameters
    KIDNEY_WIDTH = 50  # mm
    KIDNEY_LENGTH = 130  # mm
    # KIDNEY_THICKNESS = 3 # cm

    # US scan parameters
    VY = 10  # mm/s
    SCAN_RANGE = 120  # mm
    T_total = SCAN_RANGE / VY  # s
    US_FRAME = 20  # ms
    dt = US_FRAME / 1e3  # s

    yc = 0

    # t = 0:dt:T_total
    t = np.arange(0, T_total, dt)

    # 1. kidney_displacement
    v_kidney_displacement = np.vectorize(kidney_displacement)
    x_kidney_t = v_kidney_displacement(t, A, T, VARPHI)

    # 2. y of the US scan
    y_us_t = SCAN_RANGE / 2 - VY * t

    # 3. kidney edge x value in US scan
    v_ellipse_x = np.vectorize(ellipse_x)
    x_ellipse_t = v_ellipse_x(y_us_t, KIDNEY_LENGTH / 2, KIDNEY_WIDTH / 2)  # ellipse x at time t
    x_ellipse_us_t = np.reshape([-x_ellipse_t + x_kidney_t, np.flip(x_ellipse_t + x_kidney_t)], (1, -1))
    xy_ellipse_us_t = np.vstack((x_ellipse_us_t, np.hstack((y_us_t, np.flip(y_us_t))))).T
    xy_ellipse_us_t = xy_ellipse_us_t[~np.isnan(xy_ellipse_us_t).any(axis=1)]  # remove nan
    ellipse_scan_t = pat.Polygon(xy_ellipse_us_t, closed=False, edgecolor='b', linestyle='-.', fill=False, linewidth=2)

    fig, ax = plt.subplots(figsize=(14, 5))
    # t = 0, t = T_total/2, t = T_total
    draw_ellipse(ax, width=KIDNEY_LENGTH, height=KIDNEY_WIDTH,
                 xc=kidney_displacement(0, A, T, VARPHI), yc=yc,
                 edge_color='m')
    draw_ellipse(ax, width=KIDNEY_LENGTH, height=KIDNEY_WIDTH,
                 xc=kidney_displacement(T_total / 2, A, T, VARPHI), yc=yc,
                 edge_color='r', linestyle='--')
    draw_ellipse(ax, width=KIDNEY_LENGTH, height=KIDNEY_WIDTH,
                 xc=kidney_displacement(t[-1], A, T, VARPHI), yc=yc,
                 edge_color='k', linestyle='--')

    ax.add_patch(ellipse_scan_t)
    ax.axes.set_aspect('equal')

    ax.legend(["kidney at t=0", f"kidney at t={T_total / 2:.2f}", f"kidney at t={T_total:.2f}", "US Scan Edge"],
              loc="upper right")
    ax.set_title(
        f"Kidney Motion US Scan Error with A={A}cm, T={T}s"
        f", Varphi={VARPHI / 2 / np.pi:.2f}*2Pi, US frame={US_FRAME:.0f}ms"
        f", US Scan Range={SCAN_RANGE:.0f}mm")
    ax.grid()
    ax.margins(0.2, 0.2)
    # save
    folderPath = Path.cwd().joinpath("results", "3-kidney-3d-scan-error", "1.3")
    if not folderPath.exists():
        folderPath.mkdir()
    fig.savefig(folderPath.joinpath(
        f"Kidney Motion Error_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png"))  # type: ignore
    plt.show()

    print("done")


if WHICH_TEST_TO_RUN == 0:
    randomLocFixedProbe()
else:
    for _ in range(10):
        for t in [8.48, 20, 40]:
            randomLoc3DScan(t)
