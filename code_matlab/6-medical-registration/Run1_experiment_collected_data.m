clc;clear;close all
% test matlab built in algorithm with collected data
groupImages = getCollectedData();
savePath = "../../results/6-image-registration/collected_data/";
n_groups = size(groupImages,1);

robotArmDisplacement = [20,-10,30]; % mm
lc2Result = {[0.999756, 0.00234665, -20.1227, -0.000717526, 1.00076, -0.383267, 0, 0, 1],...
             [1, -1.59236e-05, 9.76066, 1.59236e-05, 1, 0.0828047, 0, 0, 1],...
             [0.998041, 0.0125403, -15.5335, -0.0131765, 0.998184, 9.86026, 0, 0, 1],...
             [0.997532, 0.0331235, 2.33827, -0.0347249, 0.999706, 2.40297, 0, 0, 1],...
             [0.99586, 0.0923258, 5.79589, -0.0929058, 0.995774, 7.31327, 0, 0, 1],...
             [1.00282, 0.0368559, 16.7501, -0.0314364, 1.00217, -0.554443, 0, 0, 1],...
             [1, -7.69316e-05, -13.3533, 7.69316e-05, 1, 7.08377, 0, 0, 1],...
             [0.998984, -0.0626777, -3.43556, 0.0625791, 0.997982, -4.78338, 0, 0, 1],...
            };
%% imregister
if ~exist(savePath,"dir")
    mkdir(savePath)
end
for groupId = 1:n_groups
    groupId
    fixedImagePath = groupImages(groupId,1);
    movingImagePath = groupImages(groupId,2);
    spacing = getDICOMSpacing(fixedImagePath) % mm / pixel

    fixedImage = dicomread(fixedImagePath);
    movingImage = dicomread(movingImagePath);
    
    if ismember(groupId,[1,2,3])
        groundTruthMatrix = [1, 0, -robotArmDisplacement(groupId);
                             0, 1, 0;
                             0, 0, 1]; % mm
    else
        groundTruthMatrix = getDICOMTransform(fixedImagePath,movingImagePath); % mm
    end

    fixedImage = pucaImageProcess(fixedImage);
    movingImage= pucaImageProcess(movingImage);
%     saveProcessedFixedMoving(fixedImage,movingImage,groupId,"../../figures/6_imageRegistration/")
    [optimizer, metric] = imregconfig("monomodal");
    optimizer.MaximumIterations = 100;
    tform = imregtform(movingImage,fixedImage,"affine",optimizer,metric); % pixel
    tform.A
    registeredImage = imwarp(movingImage,tform,"OutputView",imref2d(size(fixedImage)));
    %tform.A(1:2,3) = tform.A(1:2,3) * spacing;tform.A  % mm for display

    tform.A = groundTruthMatrix; tform.A % mm for display
    tform.A(1:2,3) = tform.A(1:2,3) / spacing; % pixel
    groundTruthRegisteredImage = imwarp(movingImage,tform,"OutputView",imref2d(size(fixedImage)));

    tform.A = reshape(lc2Result{groupId},3,3)'; % mm
    tform.A(1:2,3) = tform.A(1:2,3) / spacing; % pixel
    lc2RegisteredImage = imwarp(movingImage,tform,"OutputView",imref2d(size(fixedImage)));
    saveGroundTruthAndResult(fixedImage,movingImage, registeredImage, ...
                                 fixedImagePath,movingImagePath,...
                                 groundTruthRegisteredImage,...
                                 lc2RegisteredImage,...
                                 sprintf("imregister_%d",optimizer.MaximumIterations),...
                                 savePath)    
end
%% feature based app
groupId = randi(n_groups);
fixedImagePath = groupImages(groupId,1);
movingImagePath = groupImages(groupId,2);

fixedImage = dicomread(fixedImagePath);
movingImage = dicomread(movingImagePath);

fixedImage = pucaImageProcess(fixedImage);
movingImage= pucaImageProcess(movingImage);
%% functions
function groupImages = getCollectedData()
    imagePath = "../../data/6-image-registration/collected_data/";
    groupImageTags = string([1067,1260,1260,1475,1475,1592,...
        1795,1809,1809,1993,1993,2075,2075,2119,2119,2178]);    
    files = dir(fullfile(imagePath,"*.dcm"));

    filesNames = strings(1,length(files));
    for i=1:length(files)
        filesNames(i) = files(i).name;
    end

    groupImages = string(size(groupImageTags));
    for i=1:length(groupImageTags)
        idx = contains(filesNames,groupImageTags(i));
        groupImages(i) = files(idx).name;
    end
    groupImages = imagePath+groupImages;
    groupImages = reshape(groupImages,2,length(groupImages)/2)';
end

function image = pucaImageProcess(image)
    if size(image,3)==3
        image = rgb2gray(image);
    end
    image = image(1:635,340:1145);
% not work as expected, failed to detect contour
%     imageBw = imbinarize(image); 
%     boundaries = bwboundaries(imageBw);
%     boundary = boundaries{1};
%     mask = poly2mask(boundary(:,2), boundary(:,1), ...
%         size(image,1), size(image,2));
%     image = image .* uint8(mask);
end
function spacing = getDICOMSpacing(dicomFilePath)
    imageInfo = dicominfo(dicomFilePath);
    spacing=str2num(imageInfo.Private_0013_17xx_Creator);
end
function transformMatrix = getDICOMTransform(fixedImagePath,movingImagePath)
% read transform matrix recorded in tag 0013,0034 to 0013,0035 in image
% registration test
    fixedImageInfo = dicominfo(fixedImagePath);
    movingImageInfo = dicominfo(movingImagePath);
    matrixString = append(fixedImageInfo.Private_0013_34xx_Creator,fixedImageInfo.Private_0013_35xx_Creator);
    fixedTransformMatrix =  reshape(str2num(matrixString),4,4)';
    matrixString = append(movingImageInfo.Private_0013_34xx_Creator,movingImageInfo.Private_0013_35xx_Creator);
    movingTransformMatrix =  reshape(str2num(matrixString),4,4)';
    transformMatrix =  fixedTransformMatrix \ movingTransformMatrix
    transformMatrix(3,:) = [];
    transformMatrix(:,3) = [];
end

function saveGroundTruthAndResult(fixedImage,movingImage, registeredImage, ...
                                 fixedImagePath,movingImagePath,...
                                 groundTruthRegisteredImage,...
                                 lc2RegisteredImage,...
                                 algorithmName,savePath)
    f=figure('Position',[20,20,1000,600],'Visible','off');
    [~,fixedImageName,~] = fileparts(fixedImagePath);
    [~,movingImageName,~] = fileparts(movingImagePath);
    titleString = sprintf('groundTruth_%s_%s_%s',algorithmName,fixedImageName,movingImageName);
    sgtitle(titleString,"interpreter","none");
    subplot(2,3,1);imshow(fixedImage); title("Fixed Image")
    subplot(2,3,2);imshow(movingImage);title("Moving Image")
    subplot(2,3,3);imshow(registeredImage); title("Registered Image")
    subplot(2,3,4);imshowpair(fixedImage,groundTruthRegisteredImage,'falsecolor'); title("Ground Truth")
    subplot(2,3,5);imshowpair(fixedImage,movingImage,'falsecolor'); title("Before")
    subplot(2,3,6);imshowpair(fixedImage,registeredImage,'falsecolor'); title("After")
    saveas(f,fullfile(savePath,titleString+".png"))
    savefig(fullfile(savePath,titleString+".fig"))

    figure('Visible','off');
    img = imshowpair(fixedImage,groundTruthRegisteredImage,'falsecolor');
    titleString = sprintf('groundTruth_%s_%s',fixedImageName,movingImageName);
    imwrite(img.CData,fullfile(savePath,titleString+".png"))

    figure('Visible','off');
    img = imshowpair(fixedImage,registeredImage,'falsecolor');
    titleString = sprintf('Registration_%s_%s_%s',algorithmName,fixedImageName,movingImageName);
    imwrite(img.CData,fullfile(savePath,titleString+".png"))
    
    figure('Visible','off');
    img = imshowpair(fixedImage,lc2RegisteredImage,'falsecolor');
    titleString = sprintf('lc2_%s_%s',fixedImageName,movingImageName);
    imwrite(img.CData,fullfile(savePath,titleString+".png"))
end