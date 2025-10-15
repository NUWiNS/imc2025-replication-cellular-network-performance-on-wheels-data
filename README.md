# [IMC '25] Replication: Performance of Cellular Networks on the Wheels

In this repository, we release the dataset and scripts used in the IMC '25
paper, *Replication: Performance of Cellular Networks on the Wheels*.

<p align="center">
<img src="route_with_states_simple_replication.png" width="400"/>
</p>

**Authors**:
[[Moinak Ghoshal](https://sites.google.com/view/moinak-ghoshal/home)] 
[[Omar Basit](https://scholar.google.com/citations?user=O8YhcToAAAAJ&hl=en)] 
[[Imran Khan](https://imranbuet63.github.io)]
[[Z. Jonny Kong](https://www.jonnykong.com)]
[[Sizhe Wang](https://sizhewang.cn)]
[[Yufei Feng](https://www.linkedin.com/in/yufei-feng-7b268820b)]
[[Phuc Dinh](https://scholar.google.com/citations?user=87M0_7EAAAAJ&hl=en)]
[[Y. Charlie Hu](https://engineering.purdue.edu/~ychu/)]
[[Dimitrios Koutsonikolas](https://ece.northeastern.edu/fac-ece/dkoutsonikolas/)]

---

## Repository Structure & Usage

- **`raw_data/`**  
  Contains the original measurement data in `.xlsx` and `.csv` formats.

- **`scripts/`**  
  The scripts directory contains two types of scripts:
  1. **Process data scripts** — `parse_sa_nsa_perf_data_2023.py` and `parse_sa_nsa_perf_data_2024_lax_bos.py`  
     These scripts use the raw measurement data from the `raw_data/` directory and generate processed pickle (`.pkl`) files, which are stored in the `pkls/` folder.  
  2. **Parse data scripts** — `plot-figures.py` generates all figures presented in the ACM CoNEXT paper using both 2023 and 2024 datasets.  
     Additionally, `tmobile_nsa_sa_boston.py` and `tmobile_nsa_sa_chicago.py` generate plots specific to the head-to-head SA vs. NSA analysis conducted in Boston and Chicago.
     
- **`pkls/`**  
  Stores intermediate processed data (pickled Python objects).

- **`plots/`**  
  Contains the final parsed/visualized results, including replication figures.

---

## Data Access

Note: Use the following command to download large dataset files stored with Git LFS:
```bash
git lfs pull
```

---

## References

Please cite appropriately if you find the dataset useful.

```bibtex
@article{ghoshal:imc2025,
  title={Replication: Performance of Cellular Networks on the Wheels},
  author={Ghoshal, Moinak and Basit, Omar and Khan, Imran and Kong, Z Jonny and Wang, Sizhe and Feng, Yufei and Dinh, Phuc and Hu, Y Charlie and Koutsonikolas, Dimitrios},
  booktitle={Proceedings of the 25th ACM Internet Measurement Conference},
  year={2025}
}
```

---

If there are any questions, feel free to contact us  
([ghoshal.m@northeastern.edu](mailto:ghoshal.m@northeastern.edu)).
