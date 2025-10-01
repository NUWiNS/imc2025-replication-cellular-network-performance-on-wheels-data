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
  Contains two Python scripts for generating processed data:
  - Each script supports two flags:  
    - `--process`: Reads the raw data and stores processed output in the `pkls/` folder.  
    - `--parse`: Parses the processed data from `pkls/` and generates results/plots in the `plots/` folder.  

- **`pkls/`**  
  Stores intermediate processed data (pickled Python objects).

- **`plots/`**  
  Contains the final parsed/visualized results, including replication figures.

---

## Example Usage

Run the following commands from the repository root:

1. **Process raw data into `.pkl` files**:
   ```bash
   python scripts/coverage_script.py --process
   python scripts/performance_script.py --process
   ```

   → Processed data will be saved in the `pkls/` folder.

2. **Parse processed data and generate plots**:
   ```bash
   python scripts/coverage_script.py --parse
   python scripts/performance_script.py --parse
   ```

   → Figures and results will be stored in the `plots/` folder.

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
@article{ghoshal2025performance,
  title={Replication: Performance of Cellular Networks on the Wheels},
  author={Ghoshal, Moinak and Basit, Omar and Khan, Imran and Kong, Z Jonny and Wang, Sizhe and Feng, Yufei and Dinh, Phuc and Hu, Y Charlie and Koutsonikolas, Dimitrios},
  booktitle={Proceedings of the 25th ACM Internet Measurement Conference},
  year={2025}
}
```

---

If there are any questions, feel free to contact us  
([ghoshal.m@northeastern.edu](mailto:ghoshal.m@northeastern.edu)).
