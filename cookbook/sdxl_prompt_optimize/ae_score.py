from pathlib import Path
import torch
import torch.nn as nn
import torch.nn.functional as F
import clip
import numpy as np
from PIL import Image
import math
import os
import sys
import traceback
from platformdirs import user_cache_dir
import argparse
import csv
import time
global sorted_scores
sorted_scores = []
APP_NAME = "ae-score"
APP_AUTHOR = "rockerBOO"
model_to_host = {
    "chadscorer": "https://github.com/grexzen/SD-Chad/raw/main/chadscorer.pth",
    "sac+logos+ava1-l14-linearMSE": "https://github.com/christophschuhmann/improved-aesthetic-predictor/blob/main/sac+logos+ava1-l14-linearMSE.pth?raw=true",
}

MODEL = "sac+logos+ava1-l14-linearMSE"


def ensure_model(model=MODEL):
    """
    Make sure we have the model to score with.
    Saves into your cache directory on your system
    """
    cache_dir = user_cache_dir(APP_NAME, APP_AUTHOR)

    Path(cache_dir).mkdir(parents=True, exist_ok=True)

    file = model + ".pth"
    full_file = os.path.join(cache_dir, file)
    if not Path(full_file).exists():
        if model not in model_to_host:
            raise ValueError(
                f"invalid model: {model}. try one of these: {', '.join(model_to_host.keys())}"
            )

        url = model_to_host[model]

        import requests

        print(f"downloading {url}")
        r = requests.get(url)
        with open(full_file, "wb") as f:
            f.write(r.content)
            print(f"saved to {full_file}")


def clear_cache():
    """
    Removes all the cached models
    """
    cache_dir = user_cache_dir(APP_NAME, APP_AUTHOR)

    for f in os.listdir(cache_dir):
        os.remove(os.path.join(cache_dir, f))


def load_model(model, device="cpu"):
    ensure_model(model)
    cache_dir = user_cache_dir(APP_NAME, APP_AUTHOR)

    pt_state = torch.load(
        os.path.join(cache_dir, model + ".pth"), map_location=torch.device("cpu")
    )

    # CLIP embedding dim is 768 for CLIP ViT L 14
    predictor = AestheticPredictor(768)
    predictor.load_state_dict(pt_state)
    predictor.to(device)
    predictor.eval()

    return predictor


def load_clip_model(device="cpu"):
    clip_model, clip_preprocess = clip.load("ViT-L/14", device=device)

    return clip_model, clip_preprocess


class AestheticPredictor(nn.Module):
    def __init__(self, input_size):
        super().__init__()
        self.input_size = input_size
        self.layers = nn.Sequential(
            nn.Linear(self.input_size, 1024),
            nn.Dropout(0.2),
            # nn.ReLU()
            nn.Linear(1024, 128),
            nn.Dropout(0.2),
            # nn.ReLU()
            nn.Linear(128, 64),
            nn.Dropout(0.1),
            # nn.ReLU()
            nn.Linear(64, 16),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.layers(x)


def main(args):
    if args.device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device

    # load the model you trained previously or the model available in this repo

    print(f"Loading {args.model}")
    predictor = load_model(args.model, device)

    print("Loading CLIP ViT-L/14")
    clip_model, clip_preprocess = load_clip_model(device=device)

    def get_image_features(
        image: Image.Image, device="cpu", model=clip_model, preprocess=clip_preprocess
    ):
        image = preprocess(image).unsqueeze(0).to(device)
        with torch.no_grad():
            image_features = model.encode_image(image)
            # l2 normalize
            image_features /= image_features.norm(dim=-1, keepdim=True)
        image_features = image_features.cpu().detach().numpy()
        return image_features

    def get_score(predictor, image, device="cpu"):
        image_features = get_image_features(image, device)
        score = predictor(torch.from_numpy(image_features).to(device).float())
        return score.item()

    scores = []

    input_images = Path(args.image_file_or_dir)
    if input_images.is_dir():
        import tqdm

        list_dir = os.listdir(input_images)
        t = tqdm.tqdm(total=len(list_dir))

        for file in list_dir:
            full_file = os.path.join(input_images, file)
            if full_file.lower().endswith(
                (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".avif")
            ):
                image = Image.open(full_file)
                scores.append(
                    {"file": file, "score": get_score(predictor, image, device)}
                )
            t.update()
    else:
        if args.image_file_or_dir.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".avif")
        ):
            image = Image.open(args.image_file_or_dir)
            chad_score = get_score(predictor, image, device)
            scores.append(
                {
                    "file": args.image_file_or_dir,
                    "score": get_score(predictor, image, device),
                }
            )

    if args.save_csv:
        fieldnames = ["file", "score"]
        id = str(round(time.time()))
        csv_file = f"scores-{id}.csv"
        with open(csv_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for score in scores:
                writer.writerow(score)

            print(f"Saved CSV to {csv_file}")

    sorted_scores = sorted(scores, key=lambda x: x["score"], reverse=True)
    for score in sorted_scores:
        print(score["file"], score["score"])
    

    acc_scores = 0
    for score in sorted_scores:
        acc_scores = acc_scores + score["score"]
    print(f"average score: {acc_scores / len(sorted_scores)}")
    return acc_scores / len(sorted_scores), sorted_scores




if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "image_file_or_dir",
        type=str,
        help="Image file or directory containing the images",
    )

    parser.add_argument(
        "--save_csv",
        default=False,
        action="store_true",
        help="Save the results to a csv file in the current directory",
    )

    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"Model to use: {', '.join(model_to_host.keys())}. Defaults to {MODEL}",
    )

    parser.add_argument(
        "--device",
        default=None,
        type=str,
        help="Device to do inference on. Options: 'cpu', 'cuda'",
    )

    args = parser.parse_args()
    
    main(args)
 