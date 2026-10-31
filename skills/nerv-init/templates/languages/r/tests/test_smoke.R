# Smoke test so the Test command passes on a fresh project. Replace it with real tests.
test_that("sample sheet has required columns", {
  sheet <- testthat::test_path("..", "config", "samples.tsv")
  header <- names(read.delim(sheet, check.names = FALSE, fileEncoding = "UTF-8-BOM"))
  missing <- setdiff(c("sample_id", "fastq_1"), header)
  expect(length(missing) == 0,
         paste("config/samples.tsv is missing required columns:", paste(missing, collapse = ", ")))
})
