import time
import copy
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error 

import torch
import torch.nn as nn
import torch.optim as optim


class Train_Test():
    def __init__(self, config):
        """
        Initialize Train_Test class

        :param config: configuration
        :type config: dictionary
        """

        self.model = config['model']
        self.parameter = config['parameter']
        self.num_epochs = self.parameter['num_epochs']
        self.device = self.parameter['device']

    def train(self, model, dataloaders):
        """
        Train the model

        :param model: initialized model
        :type model: model

        :param dataloaders: train & validation dataloaders
        :type dataloaders: dictionary

        :return: trained model
        :rtype: model
        """

        since = time.time()

        model = model.to(self.device)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=self.parameter['lr'])

        val_mse_history = []

        best_model_wts = copy.deepcopy(model.state_dict())
        best_mse = 10000000

        for epoch in range(self.num_epochs):
            if epoch == 0 or (epoch + 1) % 50 == 0:
                print()
                print('Epoch {}/{}'.format(epoch + 1, self.num_epochs))

            # 각 epoch마다 순서대로 training과 validation을 진행
            for phase in ['train', 'val']:
                if phase == 'train':
                    model.train()  # 모델을 training mode로 설정
                else:
                    model.eval()   # 모델을 validation mode로 설정

                running_loss = 0.0
                running_total = 0

                # training과 validation 단계에 맞는 dataloader에 대하여 학습/검증 진행
                for inputs, labels in dataloaders[phase]:
                    inputs = inputs.to(self.device)
                    labels = labels.to(self.device, dtype=torch.float)
                    
                    # parameter gradients를 0으로 설정
                    optimizer.zero_grad()

                    # forward
                    # training 단계에서만 gradient 업데이트 수행
                    with torch.set_grad_enabled(phase == 'train'):
                        # input을 model에 넣어 output을 도출한 후, loss를 계산함
                        outputs = model(inputs)
                        outputs = outputs.squeeze(1)
                        loss = criterion(outputs, labels)

                        # backward (optimize): training 단계에서만 수행
                        if phase == 'train':
                            loss.backward()
                            optimizer.step()

                    # batch별 loss를 축적함
                    running_loss += loss.item() * inputs.size(0)
                    running_total += labels.size(0)

                # epoch의 loss 및 accuracy 도출
                epoch_loss = running_loss / running_total

                if epoch == 0 or (epoch + 1) % 50 == 0:
                    print('{} Loss: {:.4f}'.format(phase, epoch_loss))

                # validation 단계에서 validation loss가 감소할 때마다 best model 가중치를 업데이트함
                if phase == 'val' and epoch_loss < best_mse:
                    best_mse = epoch_loss
                    best_model_wts = copy.deepcopy(model.state_dict())
                if phase == 'val':
                    val_mse_history.append(epoch_loss)

        # 전체 학습 시간 계산
        time_elapsed = time.time() - since
        print('\nTraining complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
        print('Best val MSE: {:4f}'.format(best_mse))

        # validation loss가 가장 낮았을 때의 best model 가중치를 불러와 best model을 구축함
        model.load_state_dict(best_model_wts)
        return model

    def test(self, model, test_loader):
        """
        Predict classes for test dataset based on the trained model

        :param model: best trained model
        :type model: model

        :param test_loader: test dataloader
        :type test_loader: DataLoader

        :return: predicted values
        :rtype: numpy array
        """
        
        model = model.to(self.device)
        model.eval()   # 모델을 validation mode로 설정
        
        # test_loader에 대하여 검증 진행 (gradient update 방지)
        with torch.no_grad():
            preds = []
            for inputs, labels in test_loader:
                inputs = inputs.to(self.device)
                labels = labels.to(self.device, dtype=torch.float)

                # forward
                # input을 model에 넣어 output을 도출
                outputs = model(inputs)
                
                # 예측 값 및 실제 값 축적
                preds.extend(outputs.detach().cpu().numpy())
        return np.array(preds).flatten()
    