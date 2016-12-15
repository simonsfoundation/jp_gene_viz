from jp_gene_viz import dGraph


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
    f = open(fn)
    headers = f.readline().strip().split("\t")
    G = dGraph.WGraph()
    count = 0
    for dataline in f:
        columns = dataline.strip().split("\t")
        [regulator, target, beta_s] = columns[:3]
        beta = float(beta_s)
        if threshhold is not None and  abs(beta) < threshhold:
            continue
        attributes = dict(zip(headers, columns))
        G.add_edge(regulator, target, beta, attributes)
        count += 1
        if limit is not None and count > limit:
            break
    return G

expr0 = ("../../../misc/networks/"
         "th17_whole_KC_cut_prcnt_20_num_tfs_"
         "28_sam_0_deseq_cut_0.25_Aug_8_2012_priorCut1p0.tsv")

expr1 = "../../../misc/networks/Tr1_Th17_noBatch_Th17PapCut.tsv"

def caseless_intersection_list(string_sequence_source, string_sequence_compare, use_left=True):
    source_map = lower_case_map(string_sequence_source)
    compare_map = lower_case_map(string_sequence_compare)
    common_keys = set(source_map.keys()) & set(compare_map.keys())
    result_set = set(source_map[k] for k in common_keys)
    if use_left:
        result = [x for x in string_sequence_source if x in result_set]
    else:
        result = [compare_map[x.lower()] for x in string_sequence_source if x in result_set]
    return result

def lower_case_map(string_sequence):
    return {s.lower(): s for s in string_sequence}

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
    column_names = [x.strip() for x in heading[1:].split("\t")]
    row_names = []
    all_data = []
    for dataline in f:
        data = [x.strip() for x in dataline.split("\t")]
        rowname = data[0]
        valuestr = data[1:]
        values = map(float, valuestr)
        assert len(values) == len(column_names), repr(
            (len(values), len(column_names)))
        row_names.append(rowname)
        all_data.append(values)
    return (row_names, column_names, all_data)
