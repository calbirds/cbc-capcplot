# CBC Species Plot

## About the Christmas Bird Count
The Christmas Bird Count is the nation’s longest-running community science bird project. <br>
It occurs annually between December 14 and January 5 in over 3000 count circles. <br>
More information can be found on the [Audubon website](https://www.audubon.org/community-science/christmas-bird-count).<br>

## The Putah Creek CBC
The Putah Creek CBC started in 1971 and has been held on the third Sunday of December every year since then. This count is organized and sponsored by the [Yolo Bird Alliance(https://yolobirdalliance.org/).<br>

The count is conducted by consistently covering 
10 sub-areas with 70-100 participants each year.<br>
![Count circle map](assets/count_circle.png)


## About the tool
This tool allows visualization of the Putah Creek CBC (CAPC) long-term dataset. A set of indicators and a subset of species has been added to evaluate trends in:
- Owl counts
- Fire affected species
- Climate change indicator species
- Land use change indicator species

- Project page: https://hydrospheric0.github.io/cbc-capcplot/

## Project layout

- `data/CAPC_CBC_1971_2025_v3.csv` – long-term CBC table (wide format, one column per year). The page reads this file when it loads.
  - 1971–2020: Steve Hampton's Putah Creek compiler table
  - 2021–2024: Audubon's published results (two blanks in 2024 filled from the compiler table)
  - 2025: compiled from eBird checklists of 2025-12-21 (provisional until Audubon publishes)
- `data/CAPC_v3_corrections.csv` – every cell changed from v2, with the reason
- `data/CAPC_v3_review.csv` – cells kept as they are that still need a decision
- `tools/build_capc_v3.py` – rebuilds v3 from v2 and Audubon's export, plus optional review decisions
- `index.html` – the page

## Support
If you find this tool useful, please consider supporting its development:

<a href="https://buymeacoffee.com/bartg">
	<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" width="180" />
</a>
