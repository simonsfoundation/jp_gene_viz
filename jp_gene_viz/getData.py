import dGraph


network0 = ("../../../misc/networks/"
    "Th17_Tr1_papGenes_simpATAC_Prior_50_weight_1_TFA_tau1.tsv")


def read_network(fn=network0, limit=None, threshhold=None):
    f = open(fn)
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
        if limit is not None and count>limit:
            break
    return G

expr0 = ("../../../misc/networks/"
    "th17_whole_KC_cut_prcnt_20_num_tfs_28_sam_0_deseq_cut_0.25_Aug_8_2012_priorCut1p0.tsv")

expr1 = "../../../misc/networks/Tr1_Th17_noBatch_Th17PapCut.tsv"


def read_tsv(fn=expr1):
    f = open(fn)
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
        #print ((values, column_names))
        assert len(values)==len(column_names), repr((len(values), len(column_names)))
        row_names.append(rowname.lower())
        all_data.append(values)
    return (row_names, column_names, all_data)
