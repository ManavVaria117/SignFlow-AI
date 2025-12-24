import tensorflow as tf
print("TF Version:", tf.__version__)
try:
    print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
    a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
    b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
    c = tf.matmul(a, b)
    print("Matmul result:", c)
except Exception as e:
    print("Error:", e)
