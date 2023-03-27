clc; clear; close all;
% randomly choose images from different images test groups
% very hard to play with, gave up

testImageType = "multimodal";

% get images path
if testImageType == "multimodal"
    groupImages = getTestExampleImages("multimodal");
else
    groupImages = getTestExampleImages("general");
end
n_groups = size(groupImages,1);
groupId = randi(n_groups);
fixedImagePath = groupImages(groupId,1);
movingImagePath = groupImages(groupId,2);


% read images and process
fixedImage = imread(fixedImagePath);
movingImage = imread(movingImagePath);
if size(fixedImage,3)==3
    fixedImage = rgb2gray(fixedImage);
end
if size(movingImage,3)==3
    movingImage = rgb2gray(movingImage);
end
if testImageType == "multimodal"
    % affine moving image
    affinedMovingImage = affineMovingImage(movingImage);
end