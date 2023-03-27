clc; clear; close all;
% use demon_regitration_version_8f to register multimodality medical images
% by testing result,
% demon treats the fixed image as ground truth, 
% and moves the other image to be same as the fixed, which is wrong

addpath("demon_registration_version_8f\functions\");
addpath("demon_registration_version_8f\functions_affine\");
addpath("demon_registration_version_8f\functions_nonrigid\");

run demon_registration_version_8f\compile_c_files.m
cd .

%% Test 1
groupImages = getTestExampleImages("multimodal");
savePath = "../../results/6-image-registration/multi_modal/";

if ~exist(savePath,"dir")
    mkdir(savePath)
end
n_groups = size(groupImages,1);
for groupId = 1:n_groups
    fixedImagePath = groupImages(groupId,1);
    movingImagePath = groupImages(groupId,2);
    test8f(fixedImagePath,movingImagePath,savePath);
end

%% Test 2
groupImages = getTestExampleImages("general");
savePath = "../../results/6-image-registration/algorithm_compare/";
n_groups = size(groupImages,1);
if ~exist(savePath,"dir")
    mkdir(savePath)
end

for groupId = 1:n_groups
    % read images
    fixedImagePath = groupImages(groupId,1);
    movingImagePath = groupImages(groupId,2);
    test8f(fixedImagePath,movingImagePath,savePath);
end

%% Test collected Data

%% function
function test8f(fixedImagePath, movingImagePath,savePath)
% Read two images
    I1=im2double(imread(fixedImagePath));  
    I2=im2double(imread(movingImagePath)); 
    
    % added by kx
    if size(I1,3)==3
        I1 = rgb2gray(I1);
    end
    if size(I2,3)==3
        I2 = rgb2gray(I2);
    end

    % Set static and moving image
    S=I2; M=I1;
    
    % Alpha (noise) constant
    alpha=2.5;
    
    % Velocity field smoothing kernel
    Hsmooth=fspecial('gaussian',[60 60],10);
    
    % The transformation fields
    Tx=zeros(size(M)); Ty=zeros(size(M));
    
    [Sy,Sx] = gradient(S);
    for itt=1:200
        % Difference image between moving and static image        
        try
            Idiff=M-S;
        catch
            continue
        end

        % Default demon force, (Thirion 1998)
        %Ux = -(Idiff.*Sx)./((Sx.^2+Sy.^2)+Idiff.^2);
        %Uy = -(Idiff.*Sy)./((Sx.^2+Sy.^2)+Idiff.^2);

        % Extended demon force. With forces from the gradients from both
        % moving as static image. (Cachier 1999, He Wang 2005)
        [My,Mx] = gradient(M);
        Ux = -Idiff.*  ((Sx./((Sx.^2+Sy.^2)+alpha^2*Idiff.^2))+(Mx./((Mx.^2+My.^2)+alpha^2*Idiff.^2)));
        Uy = -Idiff.*  ((Sy./((Sx.^2+Sy.^2)+alpha^2*Idiff.^2))+(My./((Mx.^2+My.^2)+alpha^2*Idiff.^2)));
 
        % When divided by zero
        Ux(isnan(Ux))=0; Uy(isnan(Uy))=0;

        % Smooth the transformation field
        Uxs=3*imfilter(Ux,Hsmooth);
        Uys=3*imfilter(Uy,Hsmooth);

        % Add the new transformation field to the total transformation field.
        Tx=Tx+Uxs;
        Ty=Ty+Uys;
        M=movepixels(I1,Tx,Ty); 
    end
    saveRegistrationImageResult(I1,I2,M,fixedImagePath,movingImagePath,...
        "demon", savePath)
   
end

