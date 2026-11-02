"""Write a 10x Genomics MEX folder (as Cell Ranger's filtered_feature_bc_matrix) deterministically."""
import gzip
from pathlib import Path

MITO = [("ENSMUSG00000064351", "mt-Co1"), ("ENSMUSG00000064341", "mt-Nd1"), ("ENSMUSG00000064367", "mt-Nd5")]


def nuclear_genes(n):
    """Nuclear mouse genes; 'Mtor' and 'Mtch1' start with 'Mt' but are not mitochondrial."""
    named = [("ENSMUSG00000028991", "Mtor"), ("ENSMUSG00000024012", "Mtch1"), ("ENSMUSG00000025902", "Sox17"),
             ("ENSMUSG00000033845", "Mrpl15"), ("ENSMUSG00000025903", "Lypla1")]
    return (named + [(f"ENSMUSG{100000 + i:011d}", f"Gm{10000 + i}") for i in range(max(0, n - len(named)))])[:n]


def features(n_nuclear):
    return MITO + nuclear_genes(n_nuclear)


def write_gz(path, text):
    with open(path, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:
        fh.write(text.encode("utf-8"))


def write_mex(folder, barcodes, feats, columns):
    """columns: one dict per cell, {feature index: count}; zero counts are omitted."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    entries = [(row + 1, col + 1, value) for col, cell in enumerate(columns)
               for row, value in sorted(cell.items()) if value]
    lines = ["%%MatrixMarket matrix coordinate integer general",
             '%metadata_json: {"software_version": "cellranger-9.0.1", "format_version": 2}',
             f"{len(feats)} {len(barcodes)} {len(entries)}"]
    lines += [f"{r} {c} {v}" for r, c, v in entries]
    write_gz(folder / "matrix.mtx.gz", "\n".join(lines) + "\n")
    write_gz(folder / "barcodes.tsv.gz", "".join(f"{b}\n" for b in barcodes))
    write_gz(folder / "features.tsv.gz", "".join(f"{gid}\t{sym}\tGene Expression\n" for gid, sym in feats))


def cell(total, n_genes, mito=0, n_nuclear=None):
    """A cell with `total` UMIs over `n_genes` detected genes, `mito` of them on mt-Co1.

    Feature indexes follow features(): 0-2 are mitochondrial, nuclear genes start at 3.
    """
    if total == 0:
        return {}
    counts = {}
    nuclear_detected = n_genes - (1 if mito else 0)
    nuclear_total = total - mito
    if mito:
        counts[0] = mito
    if nuclear_detected <= 0 or nuclear_total < nuclear_detected:
        raise ValueError(f"cannot place {total} UMIs on {n_genes} genes with {mito} mito")
    if n_nuclear is not None and nuclear_detected > n_nuclear:
        raise ValueError("more detected genes than nuclear features")
    base, extra = divmod(nuclear_total, nuclear_detected)
    for i in range(nuclear_detected):
        counts[3 + i] = base + (1 if i < extra else 0)
    return counts
