# Web Page Segmentation Project

This project is designed to segment web pages into distinct sections to improve readability and organization. It provides a command-line interface (CLI) tool called `segment_cli.py` that allows you to segment web pages based on their content. This README provides an overview of the project, its usage, and installation instructions.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Options](#options)
- [Examples](#examples)

## Introduction

Web pages often contain a mix of content, such as articles, advertisements, sidebars, and navigation menus. This project aims to improve the readability of web pages by segmenting them into distinct sections. The segmentation process separates content into meaningful blocks, making it easier for readers to focus on the main article or relevant information.

## Installation

To use this tool, follow these installation instructions:

1. Navigate to the project directory:

   ```bash
   cd models/segmentator
   ```


## Usage

You can use the `segment_cli.py` script to segment web pages. The script takes a URL or a local HTML file as input and generates segmented content.

```bash
python3 segment_cli.py -u <URL> # Use -u for URL
python3 segment_cli.py -f <file_path> # Use -f for local HTML file
```

## Options

- `-u <URL>`: Provide the URL of the web page you want to segment.
- `-f <file_path>`: Provide the path to a local HTML file that you want to segment.

## Examples

Here are some examples of how to use the `segment_cli.py` script:

1. Segment a web page by URL:

   ```bash
   python3 segment_cli.py -u https://www.example.com/article
   ```

2. Segment a local HTML file:

   ```bash
   python3 segment_cli.py -f path/to/localfile.html
   ```