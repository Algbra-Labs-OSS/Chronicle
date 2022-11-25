# Chronicle

This repository contains helper functions and detection rules that could be helpful to customers of Chronicle.

# Getting Started



| folder                                  |  description                                                                                                             |
|--------------------------------------   |--------------------------------------------------------------------------------------------------------------------------|
| [`detection_rules/`](detection_rules)   | YARA-L detection rules which can be used directly in the Chronicle _Rules Editor_                                        |
| [`helper_functions/`](helper_functions) | Helper functions to collect logs from systems where no native capability to stream to the SIEM or storage bucket exists  |


Rules can be created from the Chronicle dashboard by using the _Rules Editor_. You can copy/paste rules directly into new rules. Some rules may require modifications.


# Contributions

Creating high quality detection rules is hard enough as it is; why not contribute and benefit from rules sourced by the community?

Contributions to helper functions (e.g., pulling data from a system where a native capability does not already exist) and detection rules would be appreciated!