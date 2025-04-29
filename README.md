--------------------------------------------------------------------------------
Title: Tiger Woods Empirical Project
Author: James Hawkins
Date: 2025-04-28
--------------------------------------------------------------------------------

## Introduction

This is a data science project exploring Tiger Woods' career dominance using PGA Tour stats.  
It forms part of the Data Science in Economics module coursework.  
The project scrapes player statistics, cleans and analyzes the data, and builds a blog hosted via Quarto.

Outputs include cleaned datasets, static visualizations, and an animated video.


## Repository Overview

This repository is structured as follows:

├── README.md  
├── MakeFile 
├── index.qmd  
├── _quarto.yml  
├── data/  
│   └── (generated CSVs)  
├── scripts/  
│   └── tigerwoods.py  
├── figures/  
│   └── (generated PNGs + MP4)  
├── docs/  
│   ├── index.html  
│   ├── search.json  
│   ├── site_libs/  
│   └── figures/  
├── .gitignore  
├── debug_page.html  
└── styles.css

- **data/**: Stores generated data from scraping PGA Tour and DataGolf.
- **scripts/**: Contains the main Python script for data scraping, cleaning, and figure generation.
- **figures/**: Stores generated figures and the animated rankings video.
- **docs/**: Contains the published Quarto website (ready for GitHub Pages hosting).
- **index.qmd**: Main Quarto file for the project blog.

*Note: Data files and figures are automatically generated when running the script.*


## Running Instructions

This has been tested using Python 3.10.12 for Windows 11. Within python, a number of additional libraries are required.  These are indicated below, along with the version number used to generate original results:
   > - pandas  2.2.3
   > - matplotlib  3.10.1
   > - seaborn  0.13.2
   > - selenium  4.31.0
   > - quarto  1.7.22 
   > - ffmpeg 7.1.1

Also required is the Chrome web browser and the ChromeDriver executable.  The version of ChromeDriver must match the version of Chrome installed on your machine.  The ChromeDriver executable must be in your PATH.

**Important:** Prior to running make, the only change required is to adjust the `CHROMEDRIVER_PATH` variable in `scripts/tigerwoods.py` on line 56 to point to your local ChromeDriver installation.

In order to replicate all results, if make is available it should be sufficient to type "make" at the command line.

---
Alternatively, if make is not available, the following steps can be followed to replicate the results.

1. Run the Python script to scrape, clean, and generate figures:
```
bash
python tigerwoods.py
```
1. Render the Quarto site:
```
bash
quarto render index.qmd
```
---

Both ways will generate the cleaned datasets, figures, animation, and final blog output in the docs/ folder. The produced blog can be viewed by opening `docs/index.html` in a web browser.


## More Resources

The project pulls data from:

- [PGA Tour Statistics](https://www.pgatour.com)
- [DataGolf Rankings](https://datagolf.com)

The blog can be found at: https://jhawkins05.github.io/Just-How-Good-Was-Tiger-Woods/


## About

This repository was created by **James Hawkins**.  
For queries, please contact: [hawkins.jd@outlook.com](mailto:hawkins.jd@outlook.com)

