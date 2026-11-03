"""Write a 10x Genomics MEX folder (as Cell Ranger's filtered_feature_bc_matrix) deterministically."""
import gzip
from pathlib import Path

GEX, ADT = "Gene Expression", "Antibody Capture"
MITO = [("ENSMUSG00000064351", "mt-Co1"), ("ENSMUSG00000064341", "mt-Nd1"), ("ENSMUSG00000064367", "mt-Nd5")]
ANTIBODIES = ["CD45_TotalSeqB", "CD31_TotalSeqB", "EPCAM_TotalSeqB", "CD11b_TotalSeqB"]


def nuclear_genes(n):
    """Nuclear mouse genes; 'Mtor' and 'Mtch1' start with 'Mt' but are not mitochondrial."""
    named = [("ENSMUSG00000028991", "Mtor"), ("ENSMUSG00000024012", "Mtch1"), ("ENSMUSG00000025902", "Sox17"),
             ("ENSMUSG00000033845", "Mrpl15"), ("ENSMUSG00000025903", "Lypla1")]
    return (named + [(f"ENSMUSG{100000 + i:011d}", f"Gm{10000 + i}") for i in range(max(0, n - len(named)))])[:n]


def features(n_nuclear, n_adt=0):
    """(id, symbol, type) rows: mitochondrial genes, nuclear genes, then antibody tags."""
    genes = [(gid, sym, GEX) for gid, sym in MITO + nuclear_genes(n_nuclear)]
    tags = [(name, name, ADT) for name in ANTIBODIES[:n_adt]] if n_adt else []
    return genes + tags


def write_gz(path, text):
    with open(path, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as fh:
        fh.write(text.encode("utf-8"))


def write_mex(folder, barcodes, feats, columns, v2=False):
    """columns: one dict per cell, {feature index: count}; zero counts are omitted.

    v2 writes Cell Ranger 2's layout: plain matrix.mtx, genes.tsv (id, symbol), barcodes.tsv.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    entries = [(row + 1, col + 1, value) for col, cell in enumerate(columns)
               for row, value in sorted(cell.items()) if value]
    header = ["%%MatrixMarket matrix coordinate integer general"]
    if not v2:
        header.append('%metadata_json: {"software_version": "cellranger-9.0.1", "format_version": 2}')
    lines = header + [f"{len(feats)} {len(barcodes)} {len(entries)}"] + [f"{r} {c} {v}" for r, c, v in entries]
    matrix, codes = "\n".join(lines) + "\n", "".join(f"{b}\n" for b in barcodes)
    if v2:
        if any(f[2] != GEX for f in feats):
            raise ValueError("Cell Ranger 2 folders hold genes only")
        (folder / "matrix.mtx").write_bytes(matrix.encode("utf-8"))
        (folder / "barcodes.tsv").write_bytes(codes.encode("utf-8"))
        (folder / "genes.tsv").write_bytes("".join(f"{gid}\t{sym}\n" for gid, sym, _ in feats).encode("utf-8"))
        return
    write_gz(folder / "matrix.mtx.gz", matrix)
    write_gz(folder / "barcodes.tsv.gz", codes)
    write_gz(folder / "features.tsv.gz", "".join(f"{gid}\t{sym}\t{kind}\n" for gid, sym, kind in feats))


def cell(total, n_genes, mito=0, n_nuclear=None, adt=0, n_adt=0):
    """A cell with `total` gene UMIs over `n_genes` detected genes, `mito` of them on mt-Co1,
    and `adt` antibody UMIs spread over the `n_adt` tags after the nuclear genes.

    Feature indexes follow features(): 0-2 are mitochondrial, nuclear genes start at 3.
    """
    counts = {}
    if adt:
        if not (n_adt and n_nuclear):
            raise ValueError("antibody counts need n_adt and n_nuclear")
        base, extra = divmod(adt, n_adt)
        counts.update({3 + n_nuclear + k: base + (1 if k < extra else 0) for k in range(n_adt)})
    if total == 0:
        return counts
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
