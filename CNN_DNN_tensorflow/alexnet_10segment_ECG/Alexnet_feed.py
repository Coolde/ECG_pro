import os.path
import time

import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
from sklearn.metrics import classification_report,accuracy_score #模型准确率,查准率，查全率,f1_score

import input_data
import Alexnet_ecg_model


# 命令行参数
flags = tf.app.flags
FLAGS = flags.FLAGS
flags.DEFINE_float('learning_rate', 0.01, 'Initial learning rate.')
flags.DEFINE_integer('max_steps', 8000, 'Number of steps to run trainer.')

flags.DEFINE_integer('batch_size', 256, 'Batch size.  '
                     'Must divide evenly into the dataset sizes.')
flags.DEFINE_string('train_dir', r'D:\aa_learning\pypro\python3-practice\ECG_classification\dnn_cnn\Alexnet_ecg_model', 'Directory to put the training data.')
flags.DEFINE_string('train_restore_dir', r'D:\aa_work\test_log\ECG_v1\test4\events', 'Directory to restore the training data.')
flags.DEFINE_string('restore',True, 'Directory to restore the training data.')
LAST_BEST=None

#生成占位符函数
def placeholder_inputs(batch_size):
  """
  Args:
    batch_size: The batch size will be baked into both placeholders.

  Returns:
    images_placeholder: Images placeholder.
    labels_placeholder: Labels placeholder.
  """
  images_placeholder = tf.placeholder(tf.float32, shape=(None,
                                                         Alexnet_ecg_model.IMAGE_SIZE_w))
  labels_placeholder = tf.placeholder(tf.int32, shape=(None,Alexnet_ecg_model.NUM_CLASSES/Alexnet_ecg_model.TYPE_USED))
  return images_placeholder, labels_placeholder

#字典输入
def fill_feed_dict(data_set, images_pl, labels_pl):
  """
  Args:
    data_set: The set of images and labels, from input_data.read_data_sets()
    images_pl: The images placeholder, from placeholder_inputs().
    labels_pl: The labels placeholder, from placeholder_inputs().

  Returns:
    feed_dict: The feed dictionary mapping from placeholders to values.
  """
  # Create the feed_dict for the placeholders filled with the next
  # `batch size ` examples.
  images_feed, labels_feed = data_set.next_batch(FLAGS.batch_size)
  feed_dict = {
      images_pl: images_feed,
      labels_pl: labels_feed,
  }
  return feed_dict



def run_training():
  """Train MNIST for a number of steps."""
  # Get the sets of images and labels for training, validation, and
  # test on MNIST.
  
  #读取数据
  train_dataset,validation_dataset= input_data.read_data_sets()
  print('训练集：{}，{}'.format(train_dataset._images.shape,train_dataset._labels.shape))
  print('验证集：{}, {}'.format(validation_dataset._images.shape,validation_dataset._labels.shape))

  # Tell TensorFlow that the model will be built into the default Graph.
  with tf.Graph().as_default():
    
    #生成占位符
    images_placeholder, labels_placeholder = placeholder_inputs(
        FLAGS.batch_size)

    # Build a Graph that computes predictions from the inference model.
    logits = Alexnet_ecg_model.inference(images_placeholder)
    # Add to the Graph the Ops for loss calculation.
    loss = Alexnet_ecg_model.loss(logits, labels_placeholder)

    # Add to the Graph the Ops that calculate and apply gradients.
    train_op = Alexnet_ecg_model.training(loss, FLAGS.learning_rate)

    accuracy,pre_labels,new_labels,labels_true,num_examples=Alexnet_ecg_model.accuracy(logits, labels_placeholder)
    # accuracy_validation=Alexnet_ecg_model.accuracy_validation(logits, labels_placeholder)
    # accuracy_test=Alexnet_ecg_model.accuracy_test(logits, labels_placeholder)

    # Build the summary operation based on the TF collection of Summaries.
    # summary_op = tf.summary.merge(loss.op.name)
    Entropy_summary=tf.summary.scalar('loss', loss)
    training_summary = tf.summary.scalar("training_accuracy", accuracy)
    validation_summary = tf.summary.scalar("validation_accuracy", accuracy)

    # Add the variable initializer Op.
    init = tf.global_variables_initializer()

    # Create a saver for writing training checkpoints.
    saver = tf.train.Saver()

    # Create a session for running Ops on the Graph.
    sess = tf.Session()

    # Instantiate a SummaryWriter to output summaries and the Graph.
    summary_writer = tf.summary.FileWriter(FLAGS.train_dir, sess.graph)

    # And then after everything is built:

    # Run the Op to initialize the variables.
    sess.run(init)

    best_validation_ACCURACY=0

    if FLAGS.restore:
      if not LAST_BEST:
        print('No LAST_BEST given!!')
        exit()
      best_validation_ACCURACY=LAST_BEST
      ckpt = tf.train.get_checkpoint_state(FLAGS.train_dir)  
      saver.restore(sess, ckpt.model_checkpoint_path) 
      print('restore from :{} '.format(FLAGS.train_dir))
    # Start the training loop.
    for step in range(FLAGS.max_steps):
      start_time = time.time()

      # Fill a feed dictionary with the actual set of images and labels
      # for this particular training step.
      feed_dict = fill_feed_dict(train_dataset,
                                 images_placeholder,
                                 labels_placeholder)
      feed_dict_validation = fill_feed_dict(validation_dataset,
                                 images_placeholder,
                                 labels_placeholder)

      # Run one step of the add_percent[:,i].assign(-percent_10)model.  The return values are the activations
      # from the `train_op` (which is discarded) and the `loss` Op.  To
      # inspect the values of your Ops or variables, you may include them
      # in the list passed to sess.run() and the value tensors will be
      # returned in the tuple from the call.
      _,loss_value = sess.run([train_op,loss],
                               feed_dict=feed_dict)

      duration = time.time() - start_time

      # Write the summaries and print an overview fairly often.
      if step % 100 == 0:
        # Print status to stdout.
        print('Step %d: loss = %.2f (%.3f sec)' % (step, loss_value, duration))
        # Update the events file.
        
        #训练集准确率
        accu_train,Entropy_summary_str,training_summary_str = sess.run([accuracy,Entropy_summary,training_summary], feed_dict=feed_dict)
        
        summary_writer.add_summary(Entropy_summary_str, step)
        summary_writer.add_summary(training_summary_str, step)
        print("training accuracy: {}".format(accu_train))
        
        #验证集准确率
        accu_validation,logits_get,labels_true_val,validation_summary_str = sess.run([accuracy,logits,labels_true,validation_summary], feed_dict=feed_dict_validation)
        
        #显示logits相关信息
        # print(logits_get[:3])
        print('logits_get--->type: {},shape: {}'.format(type(logits_get),logits_get.shape))
        print('labels_true_val--->type: {},shape: {}'.format(type(labels_true_val),labels_true_val.shape))
        
        summary_writer.add_summary(validation_summary_str, step)       
        print("valid accuracy: {}".format(accu_validation))

        #summary刷新
        summary_writer.flush()

        if accu_validation>best_validation_ACCURACY:
          saver.save(sess,os.path.join(FLAGS.train_dir, 'checkpoint'),global_step=step)
          print('save one model!')
          best_validation_ACCURACY=accu_validation
      if step %500==0:

        feed_dict_all_validation = {
            images_placeholder: validation_dataset._images,
            labels_placeholder: validation_dataset._labels,
        }
        pre_labels_get,new_labels_get,num_examples_get= sess.run([pre_labels,new_labels,num_examples], feed_dict=feed_dict_all_validation)
        print('num_of all validation logits: ',num_examples_get)
        report=classification_report(pre_labels_get,new_labels_get,digits=4)
        print(report)
    print('best: {}'.format(best_validation_ACCURACY))



def main(_):
  run_training()


if __name__ == '__main__':
  tf.app.run()