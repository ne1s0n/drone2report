# drone2report
From orthophoto to summary statistics, indexes, and more.

## Usage

Clone the repository, create the conda enviroment with:

`conda env create --file environment.yml`

Actuvate the environment

`conda activate drone2report`

then fill an appropriate .ini file and run:

`python3 drone2report.py <your config .ini file>`

The idea is that you *don't* write any python code, but just fill your appropriate .ini file.

Then, if you really really want, you can write some python code (i.e. you can easily expand the pipeline with your own custom analyses).

The 
[sample_config.ini](sample_config.ini) file is self documented and should be enough easy to understand to let you start.

## The steps

The pipeline runs through three steps

- data load: one data block per image. All active images are loaded (with their accompanying shapefile). Some info are print on screen
- task(s): all active task blocks are executed on all images. Their results are saved on disk
- render(s): all renders are executed to collect and consolidate the tasks results. The results are again saved on disk

## Credits

This is a joint effort between:

[<img src="PR/crea_logo.png" width=350>](https://www.crea.gov.it/)
[<img src="PR/NPEC_logo.png" width=200>](https://www.npec.nl/)


The development has also been sponsored by the [Polyploidbreeding project](https://polyploidbreeding.ibba.cnr.it/) (PRIN 2022, Settore LS2)

[<img src="PR/polyploidbreeding_logo.png" width=200>](https://polyploidbreeding.ibba.cnr.it/)
<img src="PR/EU_logo.jpg">
