from bing_image_downloader import downloader
categories = [
    "dogs", "cats", "cars", "motorcycles", "airplanes",
    "trees", "flowers", "laptops", "mountains", "beaches"
]

for category in categories:
    print(f"Downloading images for: {category}")
    downloader.download(
        query=category,
        limit=100,
        output_dir='images',
        adult_filter_off=True,
        force_replace=False,
        timeout=60
    )

print(" Image download complete.")