%Compare data between files 
    %Folder should have scans in same plane (XY, XZ, YZ)
%Fig 1: Colourmap
%Fig 2: X = 0
%Fig 2: Y = 0

clear; close all;
dataTitle = "CompareTemp20221125";
openFolder = "C:\Users\ultrast-RE\OneDrive\Desktop\SG_Transducer_Scans";
files = dir(fullfile(openFolder, '*.xlsx'));
saveFolder = "C:\Users\ultrast-RE\OneDrive\Desktop\SG_Transducer_Scans\Plots";
dbCheck = [-6,-8,-26];

%find max point
plotDataRawArray = cell(1,length(files));
for ithFile = 1:length(files)
    file = files(ithFile);
    rawData = readmatrix(fullfile(file.folder,file.name),'Range','A1','UseExcel',true);
    plotDataRawArray{ithFile} = rawData(4:end,2:end);
end
plotDataRawAllPoints = cell2mat(plotDataRawArray);
maxPoint = max(plotDataRawAllPoints(:));

%create figures
axis1 = file.name(16);
axis2 = file.name(17);
totalFig = 3;
figName = ['Colormap',
           sprintf("%s-Axis (%s=0)",axis1,axis2),
           sprintf("%s-Axis (%s=0)",axis2,axis1)
           ];
winX = [0.5, 0.2, 0.2];
for fig = 1:totalFig
    figure('Name',figName(fig))
    f=gcf;
    f.Units = 'normalized';
    winY = 0.7;
    f.Position = [1-sum(winX(1,1:fig)),0.9-winY,winX(fig),winY];
end

%calculate number of subplots
subplotTotal = length(files);
subplotTotalCols = ceil(sqrt(subplotTotal));
subplotTotalRows = subplotTotal/subplotTotalCols;
subplotNow = 0;

%plot
for ithFile = 1:length(files)
    file = files(ithFile);
    rawData = readmatrix(fullfile(file.folder,file.name));
    plotDataRaw = rawData(4:end,2:end);
    plotData = plotDataRaw/maxPoint;
    xAxisRelFP = rawData(3,2:end);
    yAxisRelFP = rawData(4:end,1);
    fp = rawData(2,3:5);
    fpCurrent = [0,0];
    switch axis1
        case 'X'
            xAxis = xAxisRelFP+fp(1);
            fpCurrent(1) = fp(1);
        case 'Y'
            xAxis = xAxisRelFP+fp(2);
            fpCurrent(1) = fp(2);
    end
    switch axis2
        case 'Y'
            yAxis = yAxisRelFP+fp(2);
            fpCurrent(2) = fp(2);
        case 'Z'
            yAxis = yAxisRelFP+fp(3);
            fpCurrent(1) = fp(3);
    end
    
    %%colormap
    subplotNow = subplotNow+1;
    figure(1)
    subplot(subplotTotalRows, subplotTotalCols, subplotNow)
    plotDataDB = 20*log10(plotData);
    imagesc(xAxis,yAxis,plotDataDB);
    colorbar;
    colormap('jet');
    hold on
    plot(fpCurrent(1),fpCurrent(2), 'x','Color', 'y','LineWidth', 1.5)
    %set axis
    ax = gca;
    axis equal;
    ax.XLim = [xAxis(1), xAxis(end)];
    ax.YLim = [yAxis(1), yAxis(end)];
    %dB line
    plotDataDB = 20*log10(plotData);
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
    
    colormapLegend{1} = sprintf("FP: (%0.2f, %0.2f ,%0.2f)",fp(1),fp(2),fp(3));
    legend(colormapLegend,'location','southoutside');
    %title, axis label
    title(sprintf("%s in dB",file.name(16:end-5)),'interpreter','none');
    xlabel(sprintf("%s Axis/mm",axis1))
    ylabel(sprintf("%s Axis/mm",axis2))
    hold off
    
    %Axis 1, y=0, save data
    [~,minIdx] = min(abs(yAxisRelFP));
    xAxisPlotData{ithFile} = plotDataDB(minIdx,:);
    %Axis 2, x=0, save data
    [~,minIdx] = min(abs(xAxisRelFP));
    yAxisPlotData{ithFile} = plotDataDB(:,minIdx);  
    filesLegend{ithFile} = file.name(16:end-5);
end

%Axis 1, y=0, plot
figure(2)
for ithFile = 1:length(files)
    plot(xAxisRelFP,cell2mat(xAxisPlotData(ithFile)));
    hold on 
end
hold off
grid on
title(sprintf("%s-Axis (%s = 0)",axis1,axis2));
xlabel(sprintf("Distance from FP in %s Axis/mm",axis1))
ylabel("Acoustic Pressure/dB")
legend(filesLegend,'Interpreter', 'none')

%Axis 2, x=0, plot
figure(3)
for ithFile = 1:length(files)
    plot(cell2mat(yAxisPlotData(ithFile)), yAxisRelFP);
    hold on 
end
hold off
grid on 
title(sprintf("%s-Axis (%s = 0)",axis2,axis1));
xlabel("Acoustic Pressure/dB")
ylabel(sprintf("Distance from FP in %s Axis/mm",axis2))
legend(filesLegend,'Interpreter', 'none')

%%save image
if ~exist(saveFolder, 'dir')
   mkdir(saveFolder)
end
for fig = 1:totalFig
    saveFile = sprintf("%s_%s%s_%s.fig", dataTitle,axis1,axis2,figName(fig));
    saveas(figure(fig), fullfile(saveFolder,saveFile));
    saveFile = sprintf("%s_%s%s_%s.png", dataTitle,axis1,axis2,figName(fig));
    saveas(figure(fig), fullfile(saveFolder,saveFile));
end
fprintf("DONE\n")