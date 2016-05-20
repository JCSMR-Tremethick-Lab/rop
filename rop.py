import sys
import csv
import os
import argparse
import subprocess
import gzip

#codeDir
codeDir=os.path.dirname(os.path.realpath(__file__))

sys.path.append('%s/tools/biopython/biopython-1.66/' %(codeDir))
import Bio
from Bio import SeqIO # module needed for sequence input






#import pysam




####################################################################
### I/O Functions 
####################################################################

def excludeReadsFromFasta(inFasta,reads,outFasta):

    fasta_sequences = SeqIO.parse(open(inFasta),'fasta')
    with open(outFasta, "w") as f:
        for seq in fasta_sequences:
            name = seq.name
            if name not in reads:
                SeqIO.write([seq], f, "fasta")

def excludeReadsFromFastaGzip(inFasta,reads,outFasta):
    
    fasta_sequences = SeqIO.parse(open(inFasta),'fasta')
    with gzip.open(outFasta, "w") as f:
        for seq in fasta_sequences:
            name = seq.name
            if name not in reads:
                SeqIO.write([seq], f, "fasta")

####################################################################

def bam2fasta(codeDir,inFile,outFile):
    message="Convert bam to fasta"
    cmdConvertBam2Fastq="%s/tools/bamtools convert -in %s -format fasta >%s" %(codeDir,inFile,outFile)
    write2Log(cmdConvertBam2Fastq,cmdLogfile,"False")
    os.system(cmdConvertBam2Fastq)

####################################################################

def bam2fastq(codeDir,inFile,outFile):
    message="Convert bam to fastq"
    write2Log(message,gLogfile,args.quiet)
    cmdConvertBam2Fastq="%s/tools/bamtools convert -in %s -format fastq >%s" %(codeDir,inFile,outFile)
    write2Log(cmdConvertBam2Fastq,cmdLogfile,"False")
    os.system(cmdConvertBam2Fastq)
    if not args.dev:
        os.remove(inFile)

#######################################################################

def write2Log(message,logFile,option):
    if not option:
        print message
    logFile.write(message)
    logFile.write("\n")

#######################################################################

def write_gzip_into_readable(gz_input, output): 
    temp_file = open(output, 'w')
    with gzip.open(gz_input, 'r') as f:
        temp_file.write(f.read())
    temp_file.close()

#######################################################################

def nReadsImmune(inFile):
    readsImmune=set()
    with open(inFile,'r') as f:
        reader=csv.reader(f,delimiter='\t')
        for line in reader:
                read=line[1]
                eValue=float(line[10])
                if eValue<1e-05:
                    readsImmune.add(read)
    return readsImmune

#######################################################################

def nMicrobialReads(inFile,readLength,outFile):
    readsMicrobiome=set()
    out=open(outFile,'w')
    with open(inFile,'r') as f:
        reader=csv.reader(f,delimiter='\t')
        for line in reader:
            read=line[0]
            identity=float(line[2])
            alignmentLength=float(line[3])
            eValue=float(line[10])
            if eValue<1e-05 and alignmentLength>=0.8*readLength and identity>=0.9*readLength:
                readsMicrobiome.add(read)
                out.write('\t'.join(line))
                out.write("\n")
    out.close()
    return readsMicrobiome

#######################################################################

print "*********************************************"
print "ROP (version 1.0.1) is a computational protocol aimed to discover the source of all reads, originated from complex RNA molecules, recombinant antibodies and microbial communities. Written by Serghei Mangul (smangul@ucla.edu) and Harry Taegyun Yang (harry2416@gmail.com), University of California, Los Angeles (UCLA). (c) 2016. Released under the terms of the General Public License version 3.0 (GPLv3)"
print ""
print "For more details see:"
print "https://sergheimangul.wordpress.com/rop/"
#print "http://serghei.bioinformatics.ucla.edu/rop/"
#print "https://github.com/smangul1/rop/ROPmanual.pdf"
print "*********************************************"

#######################################################################
### Arguments 
#######################################################################


ap = argparse.ArgumentParser('python rop.py')

necessary_arguments = ap.add_argument_group('Necessary Inputs')
necessary_arguments.add_argument('unmappedReads', help='unmapped Reads in the fastq format')
necessary_arguments.add_argument('dir', help='directory to save results of the analysis')

job_option_arguments = ap.add_argument_group('Job Options')
job_option_arguments.add_argument("--qsub", help="submit qsub jobs on hoffman2 (UCLA) cluster. If planning to use on your cluster contact smangul@ucla.edu", action="store_true")
job_option_arguments.add_argument("--qsubArray", help="prepare qsub scripts to be run later using job array. Working on hoffman2 (UCLA) cluster. If planning to use on your cluster contact smangul@ucla.edu", action="store_true")

input_option_arguments = ap.add_argument_group('Input Options')
input_option_arguments.add_argument("--b", '-b', help="unmapped reads in bam format", action="store_true")
input_option_arguments.add_argument("--fastqGz", '-z', help="unmapped reads in fasta.gz format", action="store_true")
input_option_arguments.add_argument("--skipLowq", help="skip step filtering low qulaity reads ", action="store_true")
input_option_arguments.add_argument("--skipQC", help="skip entire QC step : filtering  low-quality, low-complexity and rRNA reads", action="store_true")
input_option_arguments.add_argument("--skipPreliminary", '-s', help="skip the preliminary steps including (1) QC and (2) Remaping to human references (lost human reads)", action="store_true")



run_only_options = ap.add_argument_group('Run Options')
run_only_options.add_argument("--repeat", help = "Run lost repeat profiling ONLY", action = "store_true")
run_only_options.add_argument("--immune", help = "Run antibody profiling ONLY", action = "store_true")
run_only_options.add_argument("--metaphlan", help = "Run metaphlan profiling ONLY", action = "store_true")
run_only_options.add_argument("--circRNA", help = "Run circular RNA profiling ONLY", action="store_true")
run_only_options.add_argument("--microbiome", help = "Run microbime profiling ONLY", action = "store_true")

misc_option_arguments = ap.add_argument_group('Miscellenous Options')
misc_option_arguments.add_argument("--gzip", help = "Gzip the fasta files after filtering step", action = "store_true")
misc_option_arguments.add_argument("--quiet", help = "Suppress progress report and warnings", action = "store_true")
misc_option_arguments.add_argument("--dev", help = "Keep intermediate files", action = "store_true")
misc_option_arguments.add_argument("--nonReductive", help = "non-reductive analysis - Dev mode - Please use with caution", action = "store_true")


args = ap.parse_args()

# ONLY OPTION Configuration
# IF none of them are selected: make everything true
if not args.repeat and not args.immune and not args.circRNA and not args.microbiome:
    args.repeat = True
    args.immune = True
    args.circRNA = True
    args.microbiome = True
else:
    #It is gonna be non-reductive for now 
    args.nonReductive = True




#######################################################################
### MAIN CODE
#######################################################################

#relative path to absolute path
args.unmappedReads=os.path.abspath(args.unmappedReads)
args.dir=os.path.abspath(args.dir)


#basename
basename=os.path.splitext(os.path.basename(args.unmappedReads))[0]





#analysis directories
QCDir=args.dir+"/QC/"



humanDir=args.dir+"/human/"

lostHumanDir=humanDir+"/lostHuman/"
lostRepeatDir=humanDir+"/lostRepeat/"
bcrDir=args.dir+"/BCR/"
tcrDir=args.dir+"/TCR/"

NCL_CIRI_Dir=args.dir+"/NCL_CIRI/" 

ighDir=args.dir+"/BCR/IGH/"
igkDir=args.dir+"/BCR/IGK/"
iglDir=args.dir+"/BCR/IGL/"

tcraDir=args.dir+"/TCR/TCRA/"
tcrbDir=args.dir+"/TCR/TCRB/"
tcrdDir=args.dir+"/TCR/TCRD/"
tcrgDir=args.dir+"/TCR/TCRG/"

metaphlanDir = args.dir + "/metaphlan/"

microbiomeDir=args.dir+"/microbiome/"

bacteriaDir=args.dir+"/microbiome/bacteria/"
virusDir=args.dir+"/microbiome/virus/"
eupathdbDir=args.dir+"/microbiome/eupathdb/"



if not os.path.exists(QCDir):
    os.makedirs(QCDir)
if not os.path.exists(lostHumanDir):
    os.makedirs(lostHumanDir)
if not os.path.exists(lostRepeatDir):
    os.makedirs(lostRepeatDir)
if not os.path.exists(bcrDir):
    os.makedirs(bcrDir)
if not os.path.exists(tcrDir):
    os.makedirs(tcrDir)
if not os.path.exists(NCL_CIRI_Dir):
    os.makedirs(NCL_CIRI_Dir)
for i in [ighDir,igkDir,iglDir,tcraDir,tcrbDir,tcrdDir,tcrgDir]:
    if not os.path.exists(i):
        os.makedirs(i)
if not os.path.exists(microbiomeDir):
    os.makedirs(microbiomeDir)
if not os.path.exists(bacteriaDir):
    os.makedirs(bacteriaDir)
if not os.path.exists(virusDir):
    os.makedirs(virusDir)
if not os.path.exists(eupathdbDir):
    os.makedirs(eupathdbDir)
if not os.path.exists(metaphlanDir):
    os.makedirs(metaphlanDir)

#intermediate files
unmappedFastq=args.dir+"/unmapped_"+basename+".fastq"
lowQFile=QCDir+basename+"_lowQ.fastq"
lowQFileFasta=QCDir+basename+"_lowQ.fa"
lowQCFile=QCDir+basename+"_lowQC.fa"
rRNAFile=QCDir+basename+"_rRNA_blastFormat6.csv"
afterrRNAFasta=QCDir+basename+"_after_rRNA.fasta"

afterlostHumanFasta=lostHumanDir+basename+"_after_rRNA_lostHuman.fasta"
afterlostHumanFastaGzip=lostHumanDir+basename+"_after_rRNA_lostHuman.fasta.gz"

afterImmuneFasta=bcrDir+basename+"_afterImmune.fasta"
afterBacteraFasta=bacteriaDir+basename+"_afterBacteria.fasta"
afterVirusFasta=virusDir+basename+"_afterVirus.fasta"

metaphlan_intermediate_map = metaphlanDir + basename + "_metaphlan.map"
metaphlan_intermediate_bowtie2out = metaphlanDir + basename + "_bowtie2out.txt"
metaphlan_output = metaphlanDir + basename + "_metaphlan_output.tsv"


gBamFile=lostHumanDir+basename+"_genome.bam"
tBamFile=lostHumanDir+basename+"_transcriptome.bam"
repeatFile=lostRepeatDir+basename+"_lostRepeats_blastFormat6.csv"
afterlostRepeatFasta=lostRepeatDir+basename+"_after_lostRepeat.fasta"
NCL_CIRI_file=NCL_CIRI_Dir + basename + "_NCL_CIRI_after_bwa.sam"
after_NCL_CIRI_file_prefix = basename + "NCL_CIRI_AFTER"
ighFile=ighDir+basename+"_IGH_igblast.csv"
igkFile=igkDir+basename+"_IGK_igblast.csv"
iglFile=iglDir+basename+"_IGL_igblast.csv"
tcraFile=tcraDir+basename+"_TCRA_igblast.csv"
tcrbFile=tcrbDir+basename+"_TCRB_igblast.csv"
tcrdFile=tcrdDir+basename+"_TCRD_igblast.csv"
tcrgFile=tcrgDir+basename+"_TCRG_igblast.csv"

#log files
logQC=QCDir+basename+"_QC.log"
logrRNA=QCDir + basename + "_rRNA.log"
logHuman=lostHumanDir + basename + "_lostHuman.log"

bacteriaFile=bacteriaDir+basename+"_bacteria_blastFormat6.csv"
virusFile=virusDir+basename+"_virus_blastFormat6.csv"

bacteriaFileFiltered=bacteriaDir+basename+"_bacteriaFiltered_blastFormat6.csv"
virusFileFiltered=virusDir+basename+"_virusFiltered_blastFormat6.csv"

gLog=args.dir+"/"+basename+".log"
gLogfile=open(gLog,'w')

tLog=args.dir+"/"+"numberReads_"+basename+".log"
tLogfile=open(tLog,'w')



cmdLog=args.dir+"/"+"dev.log"
cmdLogfile=open(cmdLog,'w')


#runFiles
runLostHumanFile=lostHumanDir+"/runLostHuman_"+basename+".sh"
runLostRepeatFile=lostRepeatDir+"/runLostRepeat_"+basename+".sh"
runNCL_CIRIfile = NCL_CIRI_Dir + "/run_NCL_CIRI" + basename + ".sh" 
runIGHFile=ighDir+"/runIGH_"+basename+".sh"
runIGKFile=igkDir+"/runIGK_"+basename+".sh"
runIGLFile=iglDir+"/runIGL_"+basename+".sh"
runTCRAFile=tcraDir+"/runTCRA_"+basename+".sh"
runTCRBFile=tcrbDir+"/runTCRB_"+basename+".sh"
runTCRDFile=tcrdDir+"/runTCRD_"+basename+".sh"
runTCRGFile=tcrgDir+"/runTCRG_"+basename+".sh"
runBacteriaFile=bacteriaDir +"/runBacteria_"+basename+".sh"
runVirusFile=virusDir +"/runVirus_"+basename+".sh"
run_metaphlan_file = metaphlanDir + "/run_metaphlan_" + basename + ".sh"

os.chdir(args.dir)

#######################################################################################################################################
if args.skipQC or args.skipPreliminary:
    afterrRNAFasta=args.unmappedReads
else:
    if args.b:
        if args.skipLowq:
            bam2fasta(codeDir,args.unmappedReads,lowQFileFasta)
        else:
            bam2fastq(codeDir,args.unmappedReads,unmappedFastq)
    else :
        unmappedFastq=args.unmappedReads


    #######################################################################################################################################
    if args.skipLowq==False:
        #number of reads
        if args.fastqGz:
            with gzip.open(unmappedFastq) as f:
                for i, l in enumerate(f):
                    pass
            n=(i + 1)/4
            
            unmappedFastqGzip=unmappedFastq
            unmappedFastq=unmappedFastqGzip.split(".gz")[0]
            write_gzip_into_readable(unmappedFastqGzip,unmappedFastq)
            
            
        else:
            with open(unmappedFastq) as f:
                for i, l in enumerate(f):
                    pass
            n=(i + 1)/4

        message="Processing %s unmapped reads" %(n)
        write2Log(message,gLogfile,args.quiet)



        

        #lowQ
        write2Log("1. Quality Control...",gLogfile,args.quiet)
        cmd=codeDir+"/tools/fastq_quality_filter -v -Q 33 -q 20 -p 75 -i %s -o %s > %s \n" %(unmappedFastq,lowQFile,logQC)
        write2Log(cmd,cmdLogfile,"False")
        os.system(cmd)
        if args.b:
            os.remove(unmappedFastq)


        readLength=0
        #Convert from fastq to fasta
        fastafile=open(lowQFileFasta,'w')
        fastqfile = open(lowQFile, "rU")
        nAfterLowQReads=0
        for record in SeqIO.parse(fastqfile,"fastq"):
            readLength=len(record) #assumes the same length, will not work for Ion Torrent or Pac Bio
            fastafile.write(str(">"+record.name)+"\n")
            fastafile.write(str(record.seq)+"\n")
            nAfterLowQReads+=1
        fastafile.close()
        nLowQReads=n-nAfterLowQReads
        write2Log("--filtered %s low quality reads" %(nLowQReads) ,gLogfile,args.quiet)




    os.chdir(QCDir)
    #lowC
    cmd="export PATH=$PATH:%s/tools/seqclean-x86_64/bin" %(codeDir)
    os.system(cmd)

    cmd=codeDir+"/tools/seqclean-x86_64/seqclean %s -l 50 -M -o %s 2>>%s" %(lowQFileFasta, lowQCFile,logQC)
    write2Log(cmd,cmdLogfile,"False")
    os.system(cmd)

    cmd = "rm -rf %s/cleaning_1/ ; rm -f %s/*.cln ; rm -f %s/*.cidx; rm -f %s/*.sort" % (QCDir,QCDir,QCDir,QCDir)
    os.system(cmd)
    proc = subprocess.Popen(["grep trashed %s | awk -F \":\" '{print $2}'" %(logQC) ], stdout=subprocess.PIPE, shell=True)
    (nLowCReadsTemp, err) = proc.communicate()
    nLowCReads=int(nLowCReadsTemp.rstrip().strip())
    write2Log("--filtered %s low complexity reads (e.g. ACACACAC...)" %(nLowCReads) ,gLogfile,args.quiet)







    #rRNA
    cmd="%s/tools/blastn -task megablast -index_name %s/db/rRNA/rRNA -use_index true -query %s -db %s/db/rRNA/rRNA  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 >%s" %(codeDir,codeDir,lowQCFile,codeDir,rRNAFile)
    write2Log(cmd,cmdLogfile,"False")
    os.system(cmd)

    n_rRNATotal=0
    rRNAReads = set()
    with open(rRNAFile,'r') as f:
        reader=csv.reader(f,delimiter='\t')
        for line in reader:
            n_rRNATotal+=1
            element=line[0]
            identity=float(line[2])
            alignmentLength=float(line[3])
            eValue=float(line[10])
            if eValue<1e-05 and alignmentLength==readLength and identity>=0.94*readLength:
                rRNAReads.add(element)

    excludeReadsFromFasta(lowQCFile,rRNAReads,afterrRNAFasta)
    n_rRNAReads=len(rRNAReads)
    write2Log("--filtered %s rRNA reads" %(n_rRNAReads) ,gLogfile,args.quiet)
    write2Log("In toto : %s reads failed QC and are filtered out" %(nLowQReads+nLowCReads+n_rRNAReads) ,gLogfile,args.quiet)


    message="Number of entries in %s is %s" %(rRNAFile,n_rRNATotal)
    write2Log(message,cmdLogfile,"False")

    if not args.dev:
        os.remove(lowQFile)
        os.remove(lowQCFile)
        os.remove(lowQFileFasta)
        os.remove(rRNAFile)






#######################################################################################################################################
#2. Remaping to human references...
if not args.skipPreliminary:
    write2Log("2. Remaping to human references...",cmdLogfile,"False")
    write2Log("2. Remaping to human references...",gLogfile,args.quiet)

    cmdGenome="%s/tools/bowtie2 -k 1 -p 8 -f -x %s/db/human/Bowtie2Index/genome -U %s 2>%s | %s/tools/samtools view -SF4 -   >%s" %(codeDir,codeDir, afterrRNAFasta,logHuman,codeDir,gBamFile)

    #transcriptome
    cmdTranscriptome="%s/tools/bowtie2  -k 1 -f -p 8 -x %s/db/human/Bowtie2Index/hg19KnownGene.exon_polya200 -U %s 2>%s | %s/tools/samtools view -SF4 -  >  %s " %(codeDir,codeDir, afterrRNAFasta,logHuman, codeDir,tBamFile)
    write2Log(cmdGenome,cmdLogfile,"False")
    write2Log(cmdTranscriptome,cmdLogfile,"False")






    os.system(cmdGenome)
    os.system(cmdTranscriptome)




    nlostHumanReads_10=0

    lostHumanReads = set()


    with open(gBamFile,'r') as f:
        reader=csv.reader(f,delimiter='\t')
        for line in reader:
            if int(line[16].split(':')[2])<3:
                lostHumanReads.add(line[0])

    with open(tBamFile,'r') as f:
        reader=csv.reader(f,delimiter='\t')
        for line in reader:
            if int(line[16].split(':')[2])<3:
                lostHumanReads.add(line[0])


    if args.gzip:
        excludeReadsFromFastaGzip(afterrRNAFasta,lostHumanReads,afterlostHumanFastaGzip)
    else:
        excludeReadsFromFasta(afterrRNAFasta,lostHumanReads,afterlostHumanFasta)
    nlostHumanReads=len(lostHumanReads)
    write2Log("--identified %s lost human reads from unmapped reads " %(len(lostHumanReads)), gLogfile, args.quiet)


    if not args.dev:
        os.remove(afterrRNAFasta)
        os.remove(gBamFile)
        os.remove(tBamFile)
### TODO
else:
    if args.gzip:
        write_gzip_into_readable(args.unmappedReads,afterlostHumanFasta)
    else:
        afterlostHumanFasta = args.unmappedReads


### TODO - Branch point
if args.nonReductive:
    branch_point_file = afterlostHumanFasta
    print "Non-reductive mode selected"

#######################################################################################################################################
#3. Maping to repeat sequences...
if args.repeat:
    write2Log("3. Maping to repeat sequences...",cmdLogfile,"False")
    write2Log("3. Maping to repeat sequences...",gLogfile,args.quiet)

    #TO DO : make all fasta ->gzip
    #gzip -dc %s | , query -
    # CHANGED 
    # cmd="%s/tools/blastn -task megablast -index_name %s/db/repeats/human_repbase_20_07/human_repbase_20_07.fa -use_index true -query %s -db %s/db/repeats/human_repbase_20_07/human_repbase_20_07.fa  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 > %s" %(codeDir, codeDir, afterlostHumanFasta, codeDir, repeatFile)
    if args.nonReductive:
        input_file = branch_point_file
    else:
        input_file = afterlostHumanFasta
    cmd="%s/tools/blastn -task megablast -index_name %s/db/repeats/human_repbase_20_07/human_repbase_20_07.fa -use_index true -query %s -db %s/db/repeats/human_repbase_20_07/human_repbase_20_07.fa  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 > %s" %(codeDir, codeDir, input_file, codeDir, repeatFile)


    if args.qsub or args.qsubArray:
        f = open(runLostRepeatFile,'w')
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_lostRepeat.done \n" %(lostRepeatDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N lostRepeat -l h_data=16G,time=10:00:00 %s" %(runLostRepeatFile)
            os.system(cmdQsub)
    else:
        os.system(cmd)
        write2Log(cmd,cmdLogfile,"False")



    if not args.qsub and not args.qsubArray:

        lostRepeatReads = set()
        
        with open(repeatFile,'r') as f:
            reader=csv.reader(f,delimiter='\t')
            for line in reader:
                element=line[0]
                identity=float(line[2])
                alignmentLength=float(line[3])
                eValue=float(line[10])
                if eValue<1e-05 and alignmentLength>=0.8*readLength and identity>=0.9*readLength:
                    lostRepeatReads.add(element)

        nRepeatReads=len(lostRepeatReads)
        write2Log("-Identify %s lost repeat sequences from unmapped reads" %(nRepeatReads) ,gLogfile,args.quiet)
        write2Log("***Note : Repeat sequences classification into classes (e.g. LINE) and families (e.g. Alu) will be available in next release" ,gLogfile,args.quiet)
        excludeReadsFromFasta(afterlostHumanFasta,lostRepeatReads,afterlostRepeatFasta)

        if not args.dev:
            os.remove(afterlostHumanFasta)
else:
    print "Lost Human Repeat Profiling step is deselected - this step is skipped."

#######################################################################################################################################
#3. Non-co-linear RNA profiling
write2Log("3. Non-co-linear RNA profiling",cmdLogfile,"False")
write2Log("3. Non-co-linear RNA profiling",gLogfile,args.quiet)
write2Log("Please use --circRNA options to profile circular RNAs",gLogfile,args.quiet)
write2Log("***Note : Trans-spicing and gene fusions  are currently not supported, but will be in the next release.",gLogfile,args.quiet)


if args.circRNA:
    if args.nonReductive:   
        input_file = branch_point_file
    else:
        input_file = afterrRNAFasta
    cmd="%s/tools/bwa mem -T -S %s/db/human/BWAIndex/genome.fa %s > %s \n" %(codeDir, codeDir, input_file, NCL_CIRI_file)
    cmd = cmd + "perl %s/tools/CIRI_v1.2.pl -S -I %s -O %s -F %s/db/human/BWAIndex/genome.fa" %(codeDir, NCL_CIRI_file, after_NCL_CIRI_file_prefix, codeDir)
    if args.qsub or args.qsubArray:
        f = open(runNCL_CIRIfile,'w')
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_NCL_CIRI.done \n" %(NCL_CIRI_Dir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N NCL_CIRI -l h_data=8G,time=10:00:00 %s" %(runNCL_CIRIfile)
            os.system(cmdQsub)
    else:
        os.system(cmd)
else: 
    print "Non-co-linear RNA Profiling step is deselected - this step is skipped."

#######################################################################################################################################
#4. T and B lymphocytes profiling

if args.immune:
    immuneReads=set()

    write2Log("4a. B lymphocytes profiling...",cmdLogfile,"False")
    write2Log("4a. B lymphocytes profiling...",gLogfile,args.quiet)


    #IGH-------
    os.chdir(ighDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)

    if args.nonReductive:
        input_file = branch_point_file
    else:
        input_file = afterlostRepeatFasta

    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/IGHV.fa -germline_db_D %s/db/BCRTCR/IGHD.fa  -germline_db_J %s/db/BCRTCR/IGHJ.fa -query %s -outfmt 7 -evalue 1e-05  2>temp.txt | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"D\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,afterlostRepeatFasta, ighFile)
    write2Log(cmd,cmdLogfile,"False")


    if args.qsub or args.qsubArray:
        f = open(runIGHFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\"> %s/%s_igh.done \n" %(ighDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N igh -l h_data=16G,time=24:00:00 %s" %(runIGHFile)
            os.system(cmdQsub)
    else:
        os.chdir(ighDir)
        os.system(cmd)
        immuneReadsIGH=nReadsImmune(ighFile)
        nReadsImmuneIGH=len(immuneReadsIGH)
        write2Log("--identified %s reads mapped to immunoglobulin heavy (IGH) locus" %(nReadsImmuneIGH) ,gLogfile,args.quiet)


    #IGK---------
    os.chdir(igkDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)

    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/IGKV.fa -germline_db_D %s/db/BCRTCR/IGHD.fa  -germline_db_J %s/db/BCRTCR/IGKJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,igkFile)
    write2Log(cmd,cmdLogfile,"False")

    if args.qsub or args.qsubArray:
        f = open(runIGKFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\"> %s/%s_igk.done \n" %(igkDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N igk -l h_data=16G,time=24:00:00 %s" %(runIGKFile)
            os.system(cmdQsub)
    else:
        os.chdir(igkDir)
        os.system(cmd)
        immuneReadsIGK=nReadsImmune(igkFile)
        nReadsImmuneIGK=len(immuneReadsIGK)
        write2Log("--identified %s reads mapped to immunoglobulin kappa (IGK) locus " %(nReadsImmuneIGK) ,gLogfile,args.quiet)
                
                
    #IGL------------
    os.chdir(iglDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)
    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/IGLV.fa -germline_db_D %s/db/BCRTCR/IGHD.fa  -germline_db_J %s/db/BCRTCR/IGLJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt  | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,iglFile)
    write2Log(cmd,cmdLogfile,"False")

    if args.qsub or args.qsubArray:
        f = open(runIGLFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_igl.done \n" %(iglDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N igl -l h_data=16G,time=24:00:00 %s" %(runIGLFile)
            os.system(cmdQsub)
    else:
        os.chdir(iglDir)
        os.system(cmd)
        immuneReadsIGL=nReadsImmune(iglFile)
        nReadsImmuneIGL=len(immuneReadsIGL)
        write2Log("--identified %s reads mapped to immunoglobulin lambda (IGL) locus" %(nReadsImmuneIGL) ,gLogfile,args.quiet)


    ##################
    ##################
    write2Log("4b. T lymphocytes profiling...",cmdLogfile,"False")
    write2Log("4b. T lymphocytes profiling...",gLogfile,args.quiet)

    #TCRA-----------------
    os.chdir(tcraDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)
    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/TRAV.fa -germline_db_D %s/db/BCRTCR/TRBD.fa  -germline_db_J %s/db/BCRTCR/TRAJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,tcraFile)
    write2Log(cmd,cmdLogfile,"False")
    if args.qsub or args.qsubArray:
        f = open(runTCRAFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_tcra.done \n"%(tcraDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N tcra -l h_data=16G,time=24:00:00 %s" %(runTCRAFile)
            os.system(cmdQsub)
    else:
        os.chdir(tcraDir)
        os.system(cmd)
        immuneReadsTCRA=nReadsImmune(tcraFile)
        nReadsImmuneTCRA=len(immuneReadsTCRA)
        write2Log("--identified %s reads mapped to T cell receptor alpha (TCRA) locus" %(nReadsImmuneTCRA) ,gLogfile,args.quiet)
                
                

    #TCRB--------------
    os.chdir(tcrbDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)
    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/TRBV.fa -germline_db_D %s/db/BCRTCR/TRBD.fa  -germline_db_J %s/db/BCRTCR/TRBJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt  | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,tcrbFile)
    write2Log(cmd,cmdLogfile,"False")
    if args.qsub or args.qsubArray:
        f = open(runTCRBFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_tcrb.done \n"%(tcrbDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N tcrb -l h_data=16G,time=24:00:00 %s" %(runTCRBFile)
            os.system(cmdQsub)
    else:
        os.chdir(tcrbDir)
        os.system(cmd)
        immuneReadsTCRB=nReadsImmune(tcrbFile)
        nReadsImmuneTCRB=len(immuneReadsTCRB)
        write2Log("--identified %s reads mapped to T cell receptor beta (TCRB) locus" %(nReadsImmuneTCRB) ,gLogfile,args.quiet)


                

    #TCRD----------------
    os.chdir(tcrdDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)
    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/TRDV.fa -germline_db_D %s/db/BCRTCR/TRBD.fa  -germline_db_J %s/db/BCRTCR/TRDJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt  | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,tcrdFile)
    write2Log(cmd,cmdLogfile,"False")
    if args.qsub or args.qsubArray:
        f = open(runTCRDFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_tcrd.done \n" %(tcrdDir, basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N tcrd -l h_data=16G,time=24:00:00 %s" %(runTCRDFile)
            os.system(cmdQsub)
    else:
        os.chdir(tcrdDir)
        os.system(cmd)
        immuneReadsTCRD=nReadsImmune(tcrdFile)
        nReadsImmuneTCRD=len(immuneReadsTCRD)
        write2Log("--identified %s reads mapped to T cell receptor delta (TCRD) locus" %(nReadsImmuneTCRD) ,gLogfile,args.quiet)


                
    #TCRG---------------------
    os.chdir(tcrgDir)
    cmd="ln -s %s//db/BCRTCR/internal_data/ ./" %(codeDir)
    os.system(cmd)
    cmd="%s/tools/igblastn -germline_db_V %s/db/BCRTCR/TRGV.fa -germline_db_D %s/db/BCRTCR/TRBD.fa  -germline_db_J %s/db/BCRTCR/TRGJ.fa -query %s -outfmt 7 -evalue 1e-05 2>temp.txt  | awk '{if($13<1e-05 && ($1==\"V\" || $1==\"J\")) print }' >%s" %(codeDir,codeDir,codeDir,codeDir,input_file,tcrgFile)
    write2Log(cmd,cmdLogfile,"False")

    if args.qsub or args.qsubArray:
        f = open(runTCRGFile,'w')
        f.write("ln -s %s//db/BCRTCR/internal_data/ ./ \n" %(codeDir))
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_tcrg.done \n" %(tcrgDir,basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N tcrg -l h_data=16G,time=24:00:00 %s" %(runTCRGFile)
            os.system(cmdQsub)
    else:
        os.chdir(tcrgDir)
        os.system(cmd)
        immuneReadsTCRG=nReadsImmune(tcrgFile)
        nReadsImmuneTCRG=len(immuneReadsTCRG)
        write2Log("--identified %s reads mapped to T cell receptor gamma locus (TCRG) locus" %(nReadsImmuneTCRG) ,gLogfile,args.quiet)

    nReadsImmuneTotal=0
    if not args.qsub and not args.qsubArray:
        nReadsImmuneTotal=nReadsImmuneIGH+nReadsImmuneIGL+nReadsImmuneIGK+nReadsImmuneTCRA+nReadsImmuneTCRB+nReadsImmuneTCRD+nReadsImmuneTCRG
        write2Log("In toto : %s reads mapped to antibody repertoire loci" %(nReadsImmuneTotal) ,gLogfile,args.quiet)
        write2Log("***Note : Combinatorial diversity of the antibody repertoire (recombinations of the of VJ gene segments)  will be available in the next release.",gLogfile,args.quiet)

        immuneReads=set().union(immuneReadsTCRA,immuneReadsTCRB,immuneReadsTCRD,immuneReadsTCRG)
        excludeReadsFromFasta(input_file,immuneReads,afterImmuneFasta)
        if not args.dev:
            os.remove(afterlostRepeatFasta)
else:
    print "Immune Profiling Step is deselected - This step is skipped."

#######################################################################################################################################
# 5. Metaphlan

#TODO 
if args.metaphlan:
    write2Log("5.  Metaphlan profiling...",cmdLogfile,"False")
    write2Log("5.  Metaphlan profiling...",gLogfile,args.quiet)
    if args.nonReductive:
        input_file = branch_point_file
    else:
        input_file = afterImmuneFasta
    cmd = "python %s/tools/metaphlan2.py %s %s --input_type multifasta --bowtie2db %s/db/metaphlan/bowtie2db/mpa -t reads_map --nproc 8 --bowtie2out %s" % (codeDir, input_file, metaphlan_intermediate_map, codeDir, metaphlan_intermediate_bowtie2out)
    cmd = cmd + "\n" + "python %s/tools/metaphlan2.py --input-type blastout %s -t rel_ab > %s" %(codeDir,metaphlan_intermediate_bowtie2out, metaphlan_output)
    write2Log(cmd,cmdLogfile,"False")

    if args.qsub or args.qsubArray:
        f= open(run_metaphlan_file, 'w')
        f.write(cmd + "\n")
        f.write("echo \"done!\" > %s/%s_metaphlan.done \n" % (metaphlanDir, basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N metaphlan -l h_data=16G,time=24:00:00 %s" %(run_metaphlan_file)
            os.system(cmdQsub)


#######################################################################################################################################
# 6. Microbiome profiling...
if args.microbiome:
    write2Log("6.  Microbiome profiling...",cmdLogfile,"False")
    write2Log("6.  Microbiome profiling...",gLogfile,args.quiet)
    
    if args.nonReductive:
        input_file = branch_point_file
    else:
        input_file = afterImmuneFasta

    #bacteria ----------
    cmd="%s/tools/blastn -task megablast -index_name %s/db/microbiome/virus/virus -use_index true -query %s -db %s/db/microbiome/bacteria/bacteria  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 >%s 2>temp.txt" %(codeDir,codeDir,input_file,codeDir,bacteriaFile)
    write2Log(cmd,cmdLogfile,"False")

    if args.qsub or args.qsubArray:
        f = open(runBacteriaFile,'w')
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_bacteria.done \n"%(bacteriaDir, basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N bacteria -l h_data=16G,time=24:00:00 %s" %(runBacteriaFile)
            os.system(cmdQsub)
    else:
        os.chdir(bacteriaDir)
        os.system(cmd)
        bacteriaReads=nMicrobialReads(bacteriaFile,readLength,bacteriaFileFiltered)
        nReadsBacteria=len(bacteriaReads)
        write2Log("--identified %s reads mapped bacterial genomes" %(nReadsBacteria) ,gLogfile,args.quiet)
        excludeReadsFromFasta(afterImmuneFasta,bacteriaReads,afterBacteraFasta)
    

    #MetaPhlAn
#    cmd=" python %s/tools/metaphlan.py


#metaphlan2.py metagenome.fastq --input_type fastq
### TODO - Fix the input for non-reductive step 

    #virus-----------

    if args.qsub or args.qsubArray:
        if args.nonReductive:
            input_file = branch_point_file
        else:
            input_file = afterImmuneFasta
        cmd="%s/tools/blastn -task megablast -index_name %s/db/microbiome/virus/viruses -use_index true -query %s -db %s/db/microbiome/virus/viruses  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 >%s 2>temp" %(codeDir,codeDir,input_file,codeDir,virusFile)
        write2Log(cmd,cmdLogfile,"False")
        f = open(runVirusFile,'w')
        f.write(cmd+"\n")
        f.write("echo \"done!\">%s/%s_virus.done \n" %(virusDir, basename))
        f.close()
        if args.qsub:
            cmdQsub="qsub -cwd -V -N virus -l h_data=16G,time=24:00:00 %s" %(runVirusFile)
            os.system(cmdQsub)
    else:
        cmd="%s/tools/blastn -task megablast -index_name %s/db/microbiome/virus/viruses -use_index true -query %s -db %s/db/microbiome/virus/viruses  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 >%s 2>temp" %(codeDir,codeDir,afterBacteraFasta,codeDir,virusFile)
        write2Log(cmd,cmdLogfile,"False")
        os.chdir(virusDir)
        os.system(cmd)
        virusReads=nMicrobialReads(virusFile,readLength,virusFileFiltered)
        nReadsVirus=len(virusReads)
        write2Log("--identified %s reads mapped viral genomes" %(nReadsVirus) ,gLogfile,args.quiet)
        excludeReadsFromFasta(afterBacteraFasta,virusReads,afterVirusFasta)


    #eukaryotic pathogens----------------
    dbList=["ameoba",
            "crypto",
            "giardia",
            "microsporidia",
            "piroplasma",
            "plasmo",
            "toxo",
            "trich",
            "tritryp"]



    if args.nonReductive:
        inFasta = branch_point_file
    else:    
        inFasta = afterVirusFasta
    nReadsEP=0

    for db in dbList:
        eupathdbFile=eupathdbDir+basename+"_"+db+"_blastFormat6.csv"
        eupathdbFileFiltered=eupathdbDir+basename+"_"+db+"Filtered_blastFormat6.csv"
        runEupathdbFile=eupathdbDir+"/run_"+basename+"_"+db+".sh"


        cmd="%s/tools/blastn -task megablast -index_name %s/db/microbiome/eupathdb/%s -use_index true -query %s -db %s/db/microbiome/eupathdb/%s  -outfmt 6 -evalue 1e-05 -max_target_seqs 1 >%s 2>temp.txt" %(codeDir,codeDir,db,inFasta,codeDir,db,eupathdbFile)
        write2Log(cmd,cmdLogfile,"False")
        if args.qsub or args.qsubArray:
            f = open(runEupathdbFile,'w')
            f.write(cmd+"\n")
            f.write("echo \"done!\">%s/%s.done" %(eupathdbDir, db)+ "\n")
            f.close()
            if args.qsub:
                cmdQsub="qsub -cwd -V -N %s -l h_data=16G,time=24:00:00 %s" %(db,runEupathdbFile)
                os.system(cmdQsub)
        else:
            os.chdir(eupathdbDir)
            os.system(cmd)
            eupathdbReads=set()
            eupathdbReads=nMicrobialReads(eupathdbFile,readLength,eupathdbFileFiltered)
            nEupathdbReads=len(eupathdbReads)
            write2Log("--identified %s reads mapped %s genomes" %(nEupathdbReads,db) ,gLogfile,args.quiet)
            afterFasta=eupathdbDir+"%s_after_%s.fasta" %(basename,db)
            excludeReadsFromFasta(inFasta,eupathdbReads,afterFasta)
            inFasta=afterFasta
            nReadsEP+=nEupathdbReads


    if not args.qsub and  not args.qsubArray:
        write2Log("In toto : %s reads mapped to microbial genomes" %(nReadsBacteria+nReadsVirus+nReadsEP) ,gLogfile,args.quiet)
        nTotalReads=nLowQReads+nLowCReads+n_rRNAReads+nlostHumanReads+nRepeatReads+nReadsImmuneTotal+nReadsBacteria+nReadsVirus+nReadsEP
        write2Log("Summary:   The ROP protocol is able to account for %s reads" %(nTotalReads) ,gLogfile,args.quiet)

        message=basename+","+str(n)+","+str(nLowQReads)+","+str(nLowCReads)+","+str(n_rRNAReads)+","+str(nlostHumanReads)+","+str(nRepeatReads)+","+str(nReadsImmuneTotal)+","+str(nReadsBacteria+nReadsVirus+nReadsEP)
        tLogfile.write(message)
        tLogfile.write("\n")
else:
    print "Microbiome Profiling step is deselected - this step is skipped."



tLogfile.close()
gLogfile.close()
cmdLogfile.close()


