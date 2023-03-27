function saveProcessedFixedMoving(fixedImage, movingImage,groupId,savePath)
    imwrite(fixedImage,fullfile(savePath,sprintf("fixed_case%d.png",groupId)))
    imwrite(movingImage,fullfile(savePath,sprintf("moving_case%d.png",groupId)))
end