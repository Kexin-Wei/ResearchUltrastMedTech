function movingImage = affineMovingImage(movingImage)
    % add moving to image
    scaleFactor = 1+0.2*rand();
    theta = 20*rand();
    translation = [5*rand() 5*rand()];
    tform = simtform2d(scaleFactor,theta,translation);
    movingImage = imwarp(movingImage,tform);
end