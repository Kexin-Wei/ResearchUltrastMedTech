clc;clear;close all
% use imregister to register multimodality medical images

% INPUT
groupImages = getTestExampleImages("multimodal");
savePath = "../../results/6-image-registration/multi_modal/";

% data summary

if ~exist(savePath,"dir")
    mkdir(savePath)
end
n_groups = size(groupImages,1);
for groupId = 1:n_groups
    fixedImagePath = groupImages(groupId,1);
    movingImagePath = groupImages(groupId,2);
    imageRegistrationAndShow(fixedImagePath,movingImagePath,savePath);
end


function imageRegistrationAndShow(fixedImagePath,movingImagePath,savePath)
    fixedImage = imread(fixedImagePath);
    movingImage = imread(movingImagePath);
    if size(fixedImage,3)==3
        fixedImage = rgb2gray(fixedImage);
    end
    if size(movingImage,3)==3
        movingImage = rgb2gray(movingImage);
    end
    
    % affine moving image
    movingImage = affineMovingImage(movingImage);
    

    [optimizer, metric] = imregconfig("multimodal");
    registeredImage = imregister(movingImage,fixedImage,'affine',optimizer,metric);
    
    saveRegistrationImageResult(fixedImage,movingImage, registeredImage, ...
                                     fixedImagePath,movingImagePath,...
                                     "imregister",savePath)
end