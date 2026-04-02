from source.model.core import model_train
import pandas as pd
from sklearn.model_selection import train_test_split
from source import settings

def model_train_task():
    data = pd.read_csv(settings.settings["data"]["path"])
    seed = settings.settings.get("seed", 42)
    X = data[settings.settings["data"]["x"]].values
    y = data[settings.settings["data"]["y"]].values

    X_data, X_test, y_data, y_test  = train_test_split(X, y, test_size=0.2, random_state=seed)
    model_train(
        X_data,
        y_data,
        X_test,
        y_test
    )

    return 