"""
Parse GTF format into a JSON compatible sequence of dictionaries.

GTF format is described here:
http://useast.ensembl.org/info/website/upload/gff.html?redirect=no
"""

def gtf_attributes(attr_str):
    """
    Parse an attribute list like
    `gene_id "Rp1"; gene_name "Rp1"; p_id "P15705"; transcript_id "NM_011283";'
    into a dictionary
    """
    result = {}
    ssplit = attr_str.strip().split(";")
    for chunk in ssplit:
        chunk = chunk.strip()
        if chunk:
            kv = chunk.split(" ", 1) # ??? I guess.
            if len(kv) == 2:
                [k, v] = kv
                if v.startswith('"') and v.endswith('"'):
                    v = v[1:-1]
                result[k] = v
    return result


# Indices are 1-based in the docs; zero based here
parse = [
    (0, "seqname", str),
    (1, "source", str),
    (2, "feature", str),
    (3, "start", int),
    (4, "end", int),
    (5, "score", float),
    (6, "strand", str),
    (7, "frame", int),
    (8, "attribute", gtf_attributes),
    ]


def gtf_line_to_dict(line):
    result = {}
    line = line.strip()
    fields = line.split("\t")
    for (index, keyname, parser) in parse:
        value = None
        field = fields[index]
        if field != ".":
            value = parser(field)
        result[keyname] = value
    return result


def gtf_lines_to_dicts(lines):
    for line in lines:
        yield gtf_line_to_dict(line)


def gtf_dicts_by_gene_id(dicts, result=None):
    if result is None:
        result = {}
    for D in dicts:
        atts = D["attribute"]
        if atts:
            gene_id = atts.get("gene_id")
            if gene_id is not None:
                gene_id = gene_id.lower()
                gene_map = result.setdefault(gene_id, [])
                gene_map.append(D)
    return result


class GTFData(object):

    def __init__(self):
        self.all_dicts = []
        self.gene_id_to_dicts = {}

    def load(self, lines):
        self.all_dicts.extend(gtf_lines_to_dicts(lines))
        self.gene_id_to_dicts = gtf_dicts_by_gene_id(self.all_dicts)

    def get_gene_features(self, gene_ids, feature='exon'):
        g2d = self.gene_id_to_dicts
        result = {}
        for gene_id in gene_ids:
            dicts = g2d.get(gene_id, [])
            fdicts = [d for d in dicts if d["feature"] == feature]
            result[gene_id] = fdicts
        return result


def smoke_test():
    import pprint
    atts_s = 'gene_id "Rp1"; gene_name "Rp1"; p_id "P15705"; transcript_id "NM_011283";'
    atts = gtf_attributes(atts_s)
    pprint.pprint(atts)
    line = ('chr12\tunknown\texon\t110920407\t110920483\t.\t+\t.\tgene_id "Mir882";'
            'gene_name "Mir882"; transcript_id "NR_030540"; tss_id "TSS8654";')
    gtfdict = gtf_line_to_dict(line)
    pprint.pprint(gtfdict)
    gtfdicts = list(gtf_lines_to_dicts([line]))
    pprint.pprint(gtfdicts)

if __name__ == "__main__":
    smoke_test()
