clear; close all;
openFolder = "C:\Users\ultrast-RE\OneDrive\Desktop\SG_Transducer_Scans";
files = dir(fullfile(openFolder, '*.xlsx'));
saveFolder = "C:\Users\ultrast-RE\OneDrive\Desktop\SG_Transducer_Scans\Plots";
dbCheck = [-6,-8,-26];

for ithFile = 1:length(files)
    file = files(ithFile);
    axis1 = file.name(16);
    axis2 = file.name(17);
    rawData = readmatrix(fullfile(file.folder,file.name),'Range','A1','UseExcel',true);
    plotDataRaw = rawData(4:end,2:end); 
    plotData = plotDataRaw/max(plotDataRaw(:));
    xAxis = rawData(3,2:end);
    yAxis = rawData(4:end,1);
    figure('name', file.name(1:end-5));
    
    %%dB plot
    if axis2 == 'Z'
        subplot(2,2,[1,3])
    else
        subplot(2,3,[1,2,4,5])
    end
    plotDataDB = 20*log10(plotData);
    imagesc(xAxis,yAxis,plotDataDB);
    colorbar;
    colormap('jet');
    hold on
    plot(0,0, 'x','Color', 'y','LineWidth', 1.5)
    %set axis
    ax = gca;
    axis equal;
    ax.YDir = 'normal';
    ax.XLim = [xAxis(1), xAxis(end)];
    ax.YLim = [yAxis(1), yAxis(end)];
    colormapLegend = cell(1, 1);
    %dB line
    for ithDB = 1: length(dbCheck)
        dbRange = plotDataDB >=dbCheck(ithDB);
        [B,~] = bwboundaries(dbRange);
        %find largest area from list of outlines
        [s,d] = cellfun(@size,B);
        [~,largestAreaIdx] = max(s.*d);
        boundary = B{largestAreaIdx};
        %draw line
        boundary(end+1,:) = [1,1];
        boundary(end+1,:) = [size(plotData)];
        dbX = rescale(boundary(:,2),xAxis(1),xAxis(end));
        dbY = rescale(boundary(:,1),yAxis(1),yAxis(end));
        dbX = dbX(1:end-2,:);
        dbY = dbY(1:end-2,:);
        if min(dbX)>min(xAxis) && max(dbX)<max(xAxis) && min(dbY)>min(yAxis) && max(dbY)<max(yAxis)
            plot(dbX,dbY, 'k', 'LineWidth', 1.5)
            colormapLegend{ithDB+1} = sprintf("%ddB: %s=(%0.2f, %0.2f), %s=(%0.2f, %0.2f)", dbCheck(ithDB), axis1,min(dbX),max(dbX),axis2,min(dbY),max(dbY));
        end
    end
    %legend
    fp = rawData(2,3:5);
    colormapLegend{1} = sprintf("FP: (%0.2f, %0.2f ,%0.2f)",fp(1),fp(2),fp(3));
    legend(colormapLegend,'location','southoutside');
    %title, axis label
    title(sprintf("%s in dB",file.name(7:end-5)),'interpreter','none');
    xlabel(sprintf("Distance from FP in %s Axis/mm",axis1))
    ylabel(sprintf("Distance from FP in %s Axis/mm",axis2))
    hold off
    
    %%y=0
    if axis2 == 'Z'
        subplot(2,2,2)
    else
        subplot(2,3,3)
    end
    [~,minIdx] = min(abs(yAxis));
    plotX = plotDataDB(minIdx,:);
    plot(xAxis,plotX);
    grid on 
    yline(-6,'-','-6dB')
    yline(-8,'-','-8dB')
    yline(-26,'-','-26dB')
    xlim([min(xAxis),max(xAxis)])
    ylim([floor(min(plotX)/5)*5,ceil(max(plotX)/5)*5])
    title(sprintf("%s Axis (%s = 0)",axis1,axis2));
    xlabel(sprintf("Distance from FP in %s Axis/mm",axis1))
    ylabel("Acoustic Power/dB")
    
    %%x=0
    if axis2 == 'Z'
        subplot(2,2,4)
    else
        subplot(2,3,6)
    end
    [~,minIdx] = min(abs(xAxis));
    plotY = plotDataDB(:,minIdx);
    plot(plotY,yAxis);
    grid on 
    xline(-6,'-','-6dB')
    xline(-8,'-','-8dB')
    xline(-26,'-','-26dB')
    xlim([floor(min(plotY)/5)*5,ceil(max(plotY)/5)*5])
    ylim([min(yAxis),max(yAxis)])
    title(sprintf("%s Axis (%s = 0)",axis2,axis1));
    xlabel("Acoustic Power/dB")
    ylabel(sprintf("Distance from FP in %s Axis/mm",axis2))
    
    %%change window size
    f=gcf;
    f.Units = 'normalized';
    winX = 0.5;
    winY = 0.8;
    f.Position = [0.9-winX,0.9-winY,winX,winY];
    
    %%save image
    if ~exist(saveFolder, 'dir')
       mkdir(saveFolder)
    end
    saveFile = string(file.name(1:end-5))+'.fig';
    saveas(gcf, fullfile(saveFolder,saveFile));
    saveFile = string(file.name(1:end-5))+'.png';
    saveas(gcf, fullfile(saveFolder,saveFile));
end
fprintf("DONE\n")