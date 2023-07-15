"""
TODO: data_loader.py

This file is typically responsible for loading and preprocessing your data. It
can handle tasks such as reading data from files, performing data augmentation,
data normalization, and creating data loaders for efficient batching of the
data during training and evaluation.
"""

from PIL import Image, ImageOps
from pathlib import Path
import argparse
import configparser
import numpy as np
import os
import random


def get_files_from_subfolders(folder_path: str):
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)
    print(file_paths)


def extract_path_from_config(config_file: str):
    config = configparser.ConfigParser()
    config.read(config_file)

    unmasked_images_folder = config.get("Paths", "umasked_images_folder")
    masked_images_folder = config.get("Paths", "masked_images_folder")

    return unmasked_images_folder, masked_images_folder


def make_training_and_validation_set(dataset_size, validation_split):
    """
    Returns a training set and validation set with labels not taking
    the distribution between masked and unmasked images into account.
    This is done in one method to ensure that the same images are not used in both sets
    """
    training_set = []
    validation_set = []
    training_labels = []
    validation_labels = []

    # Using Config for better control over paths on different machines
    # see example_config.ini and rename file to labels.ini for this method to work
    unmasked_images_folder, masked_images_folder = extract_path_from_config(
        "labels.ini"
    )

    unmasked_image_files = get_files_from_subfolders(unmasked_images_folder)
    masked_image_files = get_files_from_subfolders(masked_images_folder)

    for i in range(dataset_size):
        if random.random() < 0.5:
            image_path = random.choice(unmasked_image_files)
            label = 0  # 0 for unmasked
        else:
            image_path = random.choice(masked_image_files)
            label = 1  # 1 for masked

        image = Image.open(image_path)

        if random.random() < validation_split:
            validation_set.append(image)
            validation_labels.append(label)
        else:
            training_set.append(image)
            training_labels.append(label)

    training_set = np.array(training_set)
    training_labels = np.array(training_labels)
    validation_set = np.array(validation_set)
    validation_labels = np.array(validation_labels)

    return training_set, training_labels, validation_set, validation_labels


def apply_zero_padding(image, target_size):
    new_image = Image.new(image.mode, target_size, 0)
    new_image.paste(image, (0, 0))
    return new_image


def resize_images(
    image_dir, output_dir, target_size=(256, 256), rotation=0, padding=False
):
    """
    Resize images to target size and save them to output directory.
    Currently only supports .jpg and .png images.
    It's worth noting that resize will stretch and sometimes rotate Images.
    """
    os.makedirs(output_dir, exist_ok=True)

    for image_name in os.listdir(image_dir):
        if image_name.lower().endswith((".jpg", ".png")):
            image_path = os.path.join(image_dir, image_name)
            image = Image.open(image_path)
            if padding:
                # rescale to fit to target size (retains aspect ratio)
                image = ImageOps.contain(
                    image, target_size, method=Image.Resampling.LANCZOS
                )
                image = apply_zero_padding(image, target_size)
            else:
                image = image.resize(target_size)

            prefix = Path(image_name).with_suffix("")
            suffix = Path(image_name).suffix
            if rotation:
                image = image.rotate(rotation)
                suffix = f"-rot-{rotation}{suffix}"
            output_path = os.path.join(output_dir, (f"{prefix}{suffix}"))
            image.save(output_path)


def process_dataset(input_dir, output_dir, target_size, rotate, padding):
    rotations = [90, 180, 270]
    for _, dir, _ in os.walk(input_dir):
        for d in dir:
            in_dir = os.path.abspath(os.path.join(input_dir, d))
            out_dir = os.path.abspath(os.path.join(output_dir, d))
            # base image transformation
            resize_images(in_dir, out_dir, target_size=target_size, padding=padding)
            # optional, additional rotational variations
            if rotate:
                for rotation in rotations:
                    resize_images(
                        in_dir,
                        out_dir,
                        target_size=target_size,
                        rotation=rotation,
                        padding=padding,
                    )


def main(args):
    process_dataset(
        args.input,
        args.output,
        tuple(args.size),
        args.rotate,
        args.padding,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="input directory"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./out",
        help="output directory (default: ./out)",
    )
    parser.add_argument(
        "-s",
        "--size",
        nargs=2,
        type=int,
        default=[256, 256],
        help="transformed image dimensions (w/h) (default: (256, 256))",
    )
    parser.add_argument(
        "-r",
        "--rotate",
        type=bool,
        action=argparse.BooleanOptionalAction,
        help="save additional rotated copies of source images (default: False)",
    )
    parser.add_argument(
        "-p",
        "--padding",
        type=bool,
        action=argparse.BooleanOptionalAction,
        help="apply 0-padding to images to retain aspect ratio when resizing (default: False)",
    )
    main(parser.parse_args())
