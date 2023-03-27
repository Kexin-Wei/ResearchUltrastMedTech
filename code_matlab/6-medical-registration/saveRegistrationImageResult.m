function saveRegistrationImageResult(fixedImage,movingImage, registeredImage, ...
                                     fixedImagePath,movingImagePath,...
                                     algorithmName,savePath)
    f=figure('Position',[20,20,1000,600]);
    [~,fixedImageName,~] = fileparts(fixedImagePath);
    [~,movingImageName,~] = fileparts(movingImagePath);
    titleString = sprintf('algo_%s_%s_%s',algorithmName,fixedImageName,movingImageName);
    sgtitle(titleString,"interpreter","none");
    subplot(2,3,1);imshow(fixedImage); title("Fixed Image")
    subplot(2,3,2);imshow(movingImage);title("Moving Image")
    subplot(2,3,4);imshow(registeredImage); title("Registered Image")
    subplot(2,3,5);imshowpair(fixedImage,movingImage,'falsecolor'); title("Before")
    subplot(2,3,6);imshowpair(fixedImage,registeredImage,'falsecolor'); title("After")
    saveas(f,fullfile(savePath,titleString+".png"))
end