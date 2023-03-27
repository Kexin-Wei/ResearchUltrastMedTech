%{
Tested algorithms including:
    (source:https://www.mathworks.com/help/images/image-registration.html)
    imregister	Intensity-based image registration
    imregcorr	Estimate geometric transformation that aligns two 2-D images using phase correlation
    imregdemons	Estimate displacement field that aligns two 2-D or 3-D images
%}
%% Code Description
% group_id:
%     1. e1, e2
%     2. high_reso, low_reso
%     3. p1, p2
%     4. t1, t2

clc;clear;close all

% settings
algorithm = "imregdemons"; % algorithm following above algorithm list
groupImages = getTestExampleImages("general");
savePath = "../../results/6-image-registration/algorithm_compare/";
algorithms = ["imregister","imregcorr","imregdemons"];

n_groups = size(groupImages,1);
if ~exist(savePath,"dir")
    mkdir(savePath)
end
assert(ismember(algorithm,algorithms),"No such a algorithm");

% main program

for groupId = 1:n_groups

    % read images

    fixedImagePath = groupImages(groupId,1);
    movingImagePath = groupImages(groupId,2);
    fixedImage  = imread(fixedImagePath); % gray image
    movingImage = imread(movingImagePath);

    if size(fixedImage,3)==3
        fixedImage = rgb2gray(fixedImage);
    end
    if size(movingImage,3)==3
        movingImage = rgb2gray(movingImage);
    end
    
    % optimizer setting

    if ismember(groupId,[1,3,5,6])
        [optimizer, metric] = imregconfig("monomodal");
    end
    if ismember(groupId,[2,4])
        [optimizer, metric] = imregconfig("multimodal");
    end
    
    % registration

    registeredImage = movingImage;
    switch algorithm
        case "imregister"
            if groupId == 1 || groupId == 3
                optimizer.MaximumStepLength = optimizer.MaximumStepLength*0.8;
                optimizer.MaximumIterations = 500;
            end
            registeredImage = imregister(movingImage,fixedImage,'affine',optimizer,metric);
    
        case "imregcorr"
            tformEstimate = imregcorr(movingImage,fixedImage);
            registeredImage = imwarp(movingImage,tformEstimate,'OutputView',imref2d(size(fixedImage)));
    
        case "imregdemons"
            [~,registeredImage] = imregdemons(movingImage,fixedImage,[500,400,200],'AccumulatedFieldSmoothing',1.2);
        otherwise
            fprintf("no such image registration algorihtm, registered image is same as before");
    end
    
    % display    
    saveRegistrationImageResult(fixedImage,movingImage,registeredImage,...
                                fixedImagePath,movingImagePath,algorithm,savePath)
end