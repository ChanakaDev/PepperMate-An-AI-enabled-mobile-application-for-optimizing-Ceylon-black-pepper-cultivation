# -*- coding: utf-8 -*-
"""R-02 ✅ 3. Multivariate (RNN).ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1FwN8DkoKiNvCLXN-2jiLVJNOf9Oqvmyb

# Importing libraries
"""

from google.colab import drive
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

tf.config.run_functions_eagerly(True)

"""# Data loading"""

drive.mount('/content/drive')

national_df = pd.read_csv('/content/drive/MyDrive/pepper_mate_models/price_prediction_models/all_ml_models/national_df_multivariate_models/dataset/national_df_cleaned.csv')

national_df.head()

national_df.shape

national_df.info()

"""# Extract relevant features for the multivariate model"""

features = national_df[['gr1_high_price', 'gr1_avg_price', 'gr2_high_price', 'gr2_avg_price', 'white_high_price', 'white_avg_price']]

features.head()

"""# Normalize the features"""

# Normalize the features
scaler = MinMaxScaler(feature_range=(0, 1))
normalized_features = scaler.fit_transform(features)

normalized_features

# Convert normalized data to DataFrame
normalized_features = pd.DataFrame(normalized_features, columns=features.columns)

normalized_features.head()

"""# Split the data into training and validation sets"""

# Split the data into training and validation sets
# 80 percent of 427 is: 341.6
split_time = 342
x_train = normalized_features[:split_time]
x_valid = normalized_features[split_time:]

x_train.head()

x_valid.head()

"""# Function for windowing the dataset"""

def windowed_dataset_multivariate(features, window_size, batch_size, shuffle_buffer_size):
    """
    Creates a windowed dataset for time series forecasting.

    Args:
        features: The 6 input time series data.
        window_size: The size of the sliding window.
        batch_size: The batch size for training.
        shuffle_buffer_size: The buffer size for shuffling the data.

    Returns:
        A tf.data.Dataset object representing the windowed dataset.
    """
    dataset = tf.data.Dataset.from_tensor_slices(features)
    dataset = dataset.window(window_size + 1, shift=1, drop_remainder=True)
    dataset = dataset.flat_map(lambda window: window.batch(window_size + 1))
    dataset = dataset.shuffle(shuffle_buffer_size)
    dataset = dataset.map(lambda window: (window[:-1], window[-1]))
    dataset = dataset.batch(batch_size).prefetch(1)
    return dataset

"""# Calling the windowing function to create the dataset

"""

# Set parameters for windowing
window_size = 78
batch_size = 32
shuffle_buffer_size = 1000

# Create windowed training and validation datasets
windowed_training_dataset = windowed_dataset_multivariate(x_train.values, window_size, batch_size, shuffle_buffer_size)
windowed_validation_dataset = windowed_dataset_multivariate(x_valid.values, window_size, batch_size, shuffle_buffer_size)

windowed_training_dataset

windowed_validation_dataset

"""# Model building"""

# Build the RNN model for multivariate input
model = tf.keras.models.Sequential([
    tf.keras.Input(shape=(window_size, len(features.columns))),  # Input shape with 'window_size' and '6' features
    tf.keras.layers.SimpleRNN(40, return_sequences=True),
    tf.keras.layers.SimpleRNN(40),
    tf.keras.layers.Dense(len(features.columns)),  # Output layer with 6 outputs
    tf.keras.layers.Lambda(lambda x: x * 100.0)
])

"""# Creating a callback (learning rate scheduler)"""

# lr_scheduler = tf.keras.callbacks.LearningRateScheduler(
#     lambda epoch: 1e-8 * 10**(epoch / 20)
# )

"""# Model compiling"""

# optimizer = tf.keras.optimizers.SGD(momentum = 0.9)

# Compile the model
optimizer = tf.keras.optimizers.SGD(momentum=0.9, learning_rate=1e-6)
model.compile(
    loss=tf.keras.losses.Huber(),
    metrics=['mae'],
    optimizer=optimizer
)

"""# Model training"""

# history = model.fit(windowed_training_dataset, epochs = 100, callbacks=[lr_scheduler], validation_data=windowed_validation_dataset)

# Train the model
history = model.fit(windowed_training_dataset, epochs=500, validation_data=windowed_validation_dataset)

"""# Visualizing the learning rate"""

# lrs = 1e-8 * (10 ** (np.arange(100) / 20))
# plt.semilogx(lrs, history.history["loss"])
# plt.axis([1e-8, 10e-4, 0, 20])

# plt.xlabel("Learning Rate")
# plt.ylabel("Loss")
# plt.show()

# This is a totally incorrect method of choosing a best learning rate
# Beucase I got a very high mae and loss values with this learning rate
# ===================================================================

# import matplotlib.pyplot as plt
# import numpy as np

# # Assuming 'history' is your training history object
# # and you have the learning rates in 'lrs' as calculated before

# # Find the learning rate that corresponds to the minimum loss
# min_loss_index = np.argmin(history.history['loss'])
# best_learning_rate = lrs[min_loss_index]

# print(f"Best learning rate: {best_learning_rate}")

# # Optionally, plot the loss vs. learning rate again,
# # highlighting the best learning rate
# plt.semilogx(lrs, history.history["loss"])
# plt.axis([1e-8, 1e-3, 0, 20]) # Adjust the x-axis range as needed
# plt.xlabel("Learning Rate")
# plt.ylabel("Loss")
# plt.axvline(x=best_learning_rate, color='red', linestyle='--') # Mark the best learning rate
# plt.show()

"""# Ploting the training loss and the validation loss

"""

# Plot training and validation loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper right')
plt.show()

"""# Ploting the training MAE and the validation MAE

"""

# Plot training and validation MAE
plt.plot(history.history['mae'])
plt.plot(history.history['val_mae'])
plt.title('Model MAE')
plt.ylabel('MAE')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper right')
plt.show()

"""# Forecasting the whole seriesn with the trained model

"""

# Forecasting the whole series
forecast = []
for time in range(len(normalized_features) - window_size):
    window_data = normalized_features.iloc[time:time + window_size].values
    forecast.append(model.predict(window_data[np.newaxis]))

forecast = forecast[split_time - window_size:]
results = np.array(forecast).squeeze()

"""# Plotting actual vs forecast"""

# Plotting actual vs forecast for the first time series ('gr1_high_price')
plt.figure(figsize=(20, 6))
plt.plot(x_valid.index, x_valid['gr1_high_price'], label='Actual')
plt.plot(x_valid.index, results[:, 0], label='Forecast')
plt.xlabel('Time')
plt.ylabel('gr1_high_price')
plt.title('Actual vs. Forecast gr1_high_price')
plt.legend()
plt.show()

# Plotting actual vs forecast for all features
fig, axes = plt.subplots(3, 2, figsize=(20, 18))
features_list = ['gr1_high_price', 'gr1_avg_price', 'gr2_high_price', 'gr2_avg_price', 'white_high_price', 'white_avg_price']

for i, feature in enumerate(features_list):
    ax = axes[i // 2, i % 2]
    ax.plot(x_valid.index, x_valid[feature], label='Actual')
    ax.plot(x_valid.index, results[:, i], label='Forecast')
    ax.set_xlabel('Time')
    ax.set_ylabel(feature)
    ax.set_title(f'Actual vs. Forecast {feature}')
    ax.legend()

plt.tight_layout()
plt.show()

"""# Calculating the mean absolute error"""

# Calculate mean absolute error for each feature
for i, feature in enumerate(features_list):
    mae = mean_absolute_error(x_valid[feature], results[:, i])
    print(f"Mean Absolute Error for {feature}: {mae}")

"""# Calculating the loss and accuracy"""

# Extract the final metrics from the history object
final_loss = history.history['loss'][-1]
final_val_loss = history.history['val_loss'][-1]
final_accuracy = history.history['mae'][-1]
final_val_accuracy = history.history['val_mae'][-1]

# Print the final metrics
print(f"Final Training Loss: {final_loss:.4f}")
print(f"Final Validation Loss: {final_val_loss:.4f}")
print(f"Final Training Accuracy (MAE): {final_accuracy:.4f}")
print(f"Final Validation Accuracy (MAE): {final_val_accuracy:.4f}")

from sklearn.metrics import mean_absolute_error

# Assuming `results` is the model's predictions and `x_valid` contains the actual values
# Select one target feature for MAE and Accuracy calculation
target_feature = 'gr1_high_price'

# Get the actual values corresponding to the predictions
# Assuming 'results' corresponds to the last 61 samples of x_valid
actual_values = x_valid[target_feature][-len(results):]  # Select the last 61 samples

# Get the predictions for the target feature only
# Assuming the target feature is the first column in 'results' (index 0)
# Adjust the index if it's a different column
target_predictions = results[:, x_valid.columns.get_loc(target_feature)] # Select the predictions for the target feature

# Calculate MAE
mae = mean_absolute_error(actual_values, target_predictions)
print(f"Mean Absolute Error (MAE) for {target_feature}: {mae}")

# Calculate the Mean of Actual Values
mean_actual = actual_values.mean() # Calculate mean for the selected samples
print(f"Mean of Actual Values for {target_feature}: {mean_actual}")

# Calculate Accuracy
accuracy = 1 - (mae / mean_actual)
print(f"Accuracy for {target_feature}: {accuracy:.2%}")

"""# Saving the model"""

model.save('/content/drive/MyDrive/pepper_mate_models/price_prediction_models/all_ml_models/national_df_multivariate_models/saved_models/r_02_rnn.keras')

model.save('/content/drive/MyDrive/pepper_mate_models/price_prediction_models/all_ml_models/national_df_multivariate_models/saved_models/r_02_rnn.h5')