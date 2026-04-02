import torch
from torch.utils.data import Dataset


class GPUDataset(Dataset):
    def __init__(self, X, y, scaler):
        
        if scaler:
            X = scaler.transform(X)
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]