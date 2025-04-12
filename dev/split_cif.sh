#!/bin/bash

csplit -z -f splited_ -b '%d' cif.csv /generated/ '{*}'
rm splited_0

for file in splited_{1..105}; do
    index=`grep generated ${file} | awk -F, '{print $1}'`
    [ -d ${index} ] || mkdir ${index}
    mv ${file} ${index}/generated_${index}.cif
    sed -i 's/.*"//' ${index}/generated_${index}.cif
done

grep generated cif.csv | awk -F, '{print $1}' > indices.out
NumStrcPerBatch=4
split -d -l ${NumStrcPerBatch} --additional-suffix=.txt indices.out indices_in_batch
