function groupImages = getTestExampleImages(imageType)
    assert(ismember(imageType,["general","multimodal"]),"No such image group found");
    if imageType == "general"
        imagePath = "../../data/6-image-registration/algorithm_compare/";
        groupImages = [ "e1.png","e2.png",...
                        "high_reso.png","low_reso.png",...
                        "p1.png","p2.png",...
                        "t1.png","t2.png",...
                        "brain_T1.png","brain_T1_wave.png",...
                        "brain_T2.png","brain_T2_wave.png"
                        ];
        
    
    else % imageType == "multimodal"
        imagePath="../../data/6-image-registration/multi_modal/";
        simpleModalImages = ["modtest1.png","modtest2.png"];
        brainImages = ["brain_FLAIR.png","brain_MD.png","brain_T1.png","brain_T2.png"];
        [idx1,idx2]=meshgrid(1:length(brainImages),1:length(brainImages));
        newBrainImages = [];
        pairs = [idx1(:),idx2(:)];
        for pair=pairs'
            if pair(1)>=pair(2)
                continue    
            end
            newBrainImages = [newBrainImages,brainImages(pair(1)),brainImages(pair(2))];
        end
        groupImages = [simpleModalImages,newBrainImages];
    end
    groupImages = imagePath + groupImages;
    groupImages = reshape(groupImages,2,length(groupImages)/2)';
end