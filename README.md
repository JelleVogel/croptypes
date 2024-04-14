# Reproduction of Combining Deep Learning and Street View Imagery to Map Smallholder Crop Types
Original paper can be found here: https://arxiv.org/pdf/2309.05930.pdf

CS4240 Deep Learning (2023/24 Q3) - Group 15

Authors (username, full name, student number, email address)
+ nschattenberg, Niek Schattenberg, 5121930, N.E.Schattenberg@student.tudelft.nl
+ aseremak, Aleksander Seremak, 6075401, a.k.seremak@student.tudelft.nl
+ atheocharous, Alexandros Theocharous, 5930901, a.theocharous@student.tudelft.nl
+ JelleVogel, Jelle Vogel, 4459911, J.Vogel-1@student.tudelft.nl

#Filestructure
+ `runs/`: Folder containing learning curve data of the treeNoTree classifier
+ `runs_condition/`: Folder containing learning curve data of the three condition classifier
+ `binary_tree_classifier.ipynb`: Script to train the resnet18 classifier to filter out images without a tree before classifing health condition. 
+ `get_trees_random.ipynb`: Script to randomly select trees of the generated dataset for manual annotation for the tree or no tree classifier/ filter. 
+ `images.zip`: A subset of the dataset generated to use in the pipeline. This is an example on the type of images collected. 
+ `load_data.py`: Script to generate Google Street View images of trees via the static API. 
+ `resnet18_model.pt`: Tree or no tree classifier weights.
+ `resnet50_model_balanced.pt`: Tree condition classifier weights for 3 class classification.
+ `resnet50_model_imbalance.pt`: Tree condition classifier weights for 6 class classification.
+ `treeNoTree_classification.ipynb`: Script to evaluate generated tree images with the resnet18 filter. Generate a subset of the collected images to classify the health condition on.
+ `tree_condition_classification.ipynb`: Script to train and test resnet50 classifier to classify tree health condition with sliding window voting.


# Data pipeline

First images of trees are collected via the Google Street View Static API from geolocation data. This can be done with script `load_data.py`. The script creates a directory with expert labeled annotaions as name of the subdirectories. 

Filter out images where the trees are removed at the time of imaging by Google Steet View or trees that are occluded. This filter step can be done one tree condition label folder at a time with the residual network 18 (resnet18) in `treeNoTree_classification.ipynb`. This convolutional neural network model is trained with files `get_trees_random.ipynb` and `binary_tree_classifier.ipynb`, look here for details on training the model. 

Classification of health conditions can be done with script `tree_condition_classification.ipynb`. The residual network 50 (resnet50) predicts tree health labels annotated by an expert. The model is used for 3 labels for the three most occuring labels to use about 1000 samples each (Matig, Redelijk, Slecht) to form a balanced dataset `resnet50_model_balanced.pt` or for all 6 labels and all samples with weights `resnet50_model_imbalance.pt`.

In the `runs` or `runs_condition` folders the progress of the neural networks are stored. These can be read out using tensorboard to find the accuracy and loss per epoch to see the learning process. 

