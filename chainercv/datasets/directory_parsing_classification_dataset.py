import numpy as np
import os

import chainer
from chainercv.utils import read_image


def directory_parsing_label_names(root, numerical_sort=False):
    """Get label names from the directories that are named by them.

    The label names are the names of the directories that locate a
    layer below the root directory.

    The label names can be used together with
    :class:`chainercv.datasets.DirectoryParsingClassificationDataset`.
    The index of a label name corresponds to the label id
    that is used by the dataset to refer the label.

    Args:
        root (str): The root directory.
        numerical_sort (bool): Label names are sorted numerically.
            This means that label :obj:`2` is before label :obj:`10`,
            which is not the case when string sort is used.
            The default value is :obj:`False`.

    Retruns:
        list of strings:
        Sorted names of classes.

    """
    label_names = [d for d in os.listdir(root)
                   if os.path.isdir(os.path.join(root, d))]

    if not numerical_sort:
        label_names.sort()
    else:
        label_names = sorted(label_names, key=int)
    return label_names


def _check_img_ext(path):
    img_extensions = ['.jpg', '.jpeg', '.png', '.ppm', '.bmp']
    return any(os.path.splitext(path)[1].lower() == extension for
               extension in img_extensions)


def _parse_classification_dataset(root, label_names,
                                  check_img_file=_check_img_ext):
    img_paths = []
    labels = []
    for label, label_name in enumerate(label_names):
        label_dir = os.path.join(root, label_name)
        if not os.path.isdir(label_dir):
            continue

        walk_dir = sorted(os.walk(label_dir), key=lambda x: x[0])
        for cur_dir, _, names in walk_dir:
            names = sorted(names)
            for name in names:
                img_path = os.path.join(cur_dir, name)
                if check_img_file(img_path):
                    img_paths.append(img_path)
                    labels.append(label)

    return img_paths, np.array(labels, np.int32)


class DirectoryParsingClassificationDataset(chainer.dataset.DatasetMixin):
    """A classification dataset for directories whose names are label names.

    The label names are the names of the directories that locate a layer below
    the root directory.
    All images locating under the subdirectoies will be categorized to classes
    with subdirectory names.
    An image is parsed only when the function :obj:`check_img_file`
    returns :obj:`True` by taking the path to the image as an argument.
    If :obj:`check_img_file` is :obj:`None`,
    the path with any image extensions will be parsed.

    Example:

        A directory structure should be one like below.

        .. code::

            root
            |-- class_0
            |   |-- img_0.png
            |   |-- img_1.png
            |
            --- class_1
                |-- img_0.png

        >>> from chainercv.dataset import DirectoryParsingClassificationDataset
        >>> dataset = DirectoryParsingClassificationDataset('root')
        >>> dataset.paths
        ['root/class_0/img_0.png', 'root/class_0/img_1.png',
        'root_class_1/img_0.png']
        >>> dataset.labels
        array([0, 0, 1])

    Args:
        root (str): The root directory.
        check_img_file (callable): A function to determine
            if a file should be included in the dataset.
        color (bool): If :obj:`True`, this dataset read images
            as color images.
        numerical_sort (bool): Label names are sorted numerically.
            This means that label :obj:`2` is before label :obj:`10`,
            which is not the case when string sort is used.
            Regardless of this option, string sort is used for the
            order of files with the same label.
            The default value is :obj:`False`.

    """

    def __init__(self, root, check_img_file=None, color=True,
                 numerical_sort=False):
        self.color = color

        label_names = directory_parsing_label_names(
            root, numerical_sort=numerical_sort)
        if check_img_file is None:
            check_img_file = _check_img_ext

        self.img_paths, self.labels = _parse_classification_dataset(
            root, label_names, check_img_file)

    def __len__(self):
        return len(self.img_paths)

    def get_example(self, i):
        img = read_image(self.img_paths[i], color=self.color)
        label = self.labels[i]
        return img, label
