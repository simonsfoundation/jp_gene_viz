import dGraph


network0 = ("../../../misc/networks/"
            "Th17_Tr1_papGenes_simpATAC_"
            "Prior_50_weight_1_TFA_tau1.tsv")


def read_network(fn=network0, limit=None, threshhold=None):
    """
    Read a tab delimited file containing at least 3 columns:
    regulator_name, target_name, beta_value_number.
    Return a directed graph representation linking regulators to targets with
    the specified weights.

    The first line of the file is assumed to be a header line.  It is skipped.
    """
    f = open(fn, "rU")
    headers = f.readline()
    G = dGraph.WGraph()
    count = 0
    for dataline in f:
        columns = dataline.split()
        [regulator, target, beta_s] = columns[:3]
        beta = float(beta_s)
        if abs(beta) < threshhold:
            continue
        G.add_edge(regulator.lower(), target.lower(), beta)
        count += 1
        if limit is not None and count > limit:
            break
    return G

expr0 = ("../../../misc/networks/"
         "th17_whole_KC_cut_prcnt_20_num_tfs_"
         "28_sam_0_deseq_cut_0.25_Aug_8_2012_priorCut1p0.tsv")

expr1 = "../../../misc/networks/Tr1_Th17_noBatch_Th17PapCut.tsv"


def read_tsv(fn=expr1):
    """
    Read a table of numbers in a tab separated value representation.
    The first line  gives the column names.
    The remaining lines give the row name followed by numeric entry
    values for that row.
    """
    # open with universal newline support
    f = open(fn, "rU")
    heading = f.readline()
    assert heading[0] == "\t", "expect tab first in headings " + repr(heading)
    column_names = [x.strip().lower() for x in heading[1:].split("\t")]
    row_names = []
    all_data = []
    for dataline in f:
        data = [x.strip() for x in dataline.split("\t")]
        rowname = data[0]
        valuestr = data[1:]
        values = map(float, valuestr)
        assert len(values) == len(column_names), repr(
            (len(values), len(column_names)))
        row_names.append(rowname.lower())
        all_data.append(values)
    return (row_names, column_names, all_data)
