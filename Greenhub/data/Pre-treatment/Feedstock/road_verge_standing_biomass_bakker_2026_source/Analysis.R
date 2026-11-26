if(require(rstudioapi)==0){
  install.packages('rstudioapi')
}

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))


# Biomass -----------------------------------------------------------------
library(glmmTMB)
library(DHARMa)
library(emmeans)

BM=read.csv2("Biomass.csv")

BM$Biomass=as.numeric(BM$Biomass)*10/1000 # convert to gram/m2 to tons/ha
BM$Productivity=as.numeric(scale(as.numeric(BM$Productivity))) # scale productivity variable for better model performance
BM$Month=as.factor(BM$Month)
BM$Mow=as.factor(BM$Mow)


## comparison of standing biomass in June and August of the control plot, and how this depends on the road verge productivity (average June-August productivity of not yet mown plots).
BM_aug=BM[BM$Mow=="Aug",]

LMER1=glmmTMB(log(Biomass)~ Productivity*Month+(1|Roadverge),data=BM_aug,REML=F)
LMER2=glmmTMB(log(Biomass)~ Productivity+Month+(1|Roadverge),data=BM_aug,REML=F)
LMER3=glmmTMB(log(Biomass)~ Productivity+(1|Roadverge),data=BM_aug,REML=F)

plot(simulateResiduals(LMER1))# model check --> ok

anova(LMER1,LMER2) # no interaction Productivity*Month effect
anova(LMER2,LMER3) # no Month effect

# comparison of biomass between mowing treatments for June mowing round (table 2)
BMs=na.omit(BM)
BMss=BMs[BMs$Month=='Jun',]

LMER1=glmmTMB(log(Biomass)~Mow*Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')
LMER2=glmmTMB(log(Biomass)~Mow+Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')
LMER3=glmmTMB(log(Biomass)~Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')

plot(simulateResiduals(LMER1))# model check --> ok

anova(LMER2,LMER1) # no interaction Productivity*Mow effect
anova(LMER3,LMER2) # Mow effect present

# evaluate where the effect occurs
LMER=glmmTMB(log(Biomass)~Productivity+Mow+(1|Roadverge),data=BMss)

emmeans_res <- emmeans(LMER, "Mow",type='response')
contrast((emmeans_res), list("Treatment JunAug vs Aug" = c(-1, 1,0,0,0,0),"Treatment JunhAug vs Aug"=c(-1,0,1,0,0,0),"Treatment JunhNov vs Aug" = c(-1, 0,0,1,0,0),"Treatment JunNov vs Aug"=c(-1,0,0,0,1,0),"Treatment Nov vs Aug" = c(-1, 0,0,0,0,1)))


## comparison of biomass between mowing treatments for August mowing round (table 2)
BMs=na.omit(BM)
BMss=BMs[BMs$Month=='Aug',]

LMER1=glmmTMB(log(Biomass)~Mow*Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')
LMER2=glmmTMB(log(Biomass)~Mow+Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')
LMER3=glmmTMB(log(Biomass)~Productivity+(1|Roadverge),data=BMss,REML = F,na.action='na.fail')

plot(simulateResiduals(LMER1))# model check --> not the best, although these plot do not show significant problems with the residuals. sqrt might be better, but outcomes are more difficult to interpret, not consistent with the previous analysis and if sqrt is applied instead, emmeans results are similar.

anova(LMER2,LMER1) # no interaction Productivity*Mow effect
anova(LMER3,LMER2) # Mow effect present

# evaluate where the effect occurs
LMER=glmmTMB(log(Biomass)~Productivity+Mow+(1|Roadverge),data=BMss)

emmeans_res <- emmeans(LMER, "Mow",type='response')
contrast((emmeans_res), list("Treatment JunAug vs Aug" = c(-1, 1,0,0,0,0),"Treatment JunhAug vs Aug"=c(-1,0,1,0,0,0),"Treatment JunhNov vs Aug" = c(-1, 0,0,1,0,0),"Treatment JunNov vs Aug"=c(-1,0,0,0,1,0),"Treatment Nov vs Aug" = c(-1, 0,0,0,0,1)))


## plotting biomass data to double check model outcomes (figure s6)

# option to plot relative (to treatment Aug) or absolute biomass
option='relative'

BM=read.csv2("Biomass.csv")

BM$Biomass=as.numeric(BM$Biomass)*10/1000 # convert to gram/m2 to tons/ha
BM$Productivity=as.numeric(BM$Productivity)*10/1000 # convert to gram/m2 to tons/ha
BM$Month=as.factor(BM$Month)
BM$Mow=as.factor(BM$Mow)

selected_month='Jun'

BMs=BM[BM$Month==selected_month,]
BMs=BMs[order(BMs$Roadverge),]
BMs=BMs[order(BMs$Mow),]

if(option=='relative'){
  Biomass_relative_jun=BMs$Biomass/rep(BMs$Biomas[1:10],6)*100-100
}else{
  Biomass_relative_jun=BMs$Biomass
}

selected_month='Aug'

BMs=BM[BM$Month==selected_month,]
BMs=BMs[order(BMs$Roadverge),]
BMs=BMs[order(BMs$Mow),]


if(option=='relative'){
  Biomass_relative_aug=BMs$Biomass/rep(BMs$Biomas[1:10],6)*100-100
}else{
  Biomass_relative_aug=BMs$Biomass
}

# create colors based on productivity
rd=round((BMs$Productivity-min(BMs$Productivity))/max(BMs$Productivity-min(BMs$Productivity))*100)
rd[rd==0]=1
BMs$col= rainbow(130)[rd]

# info for legend
leg=round((c(1:7)*100-min(BMs$Productivity))/max(c(1:7)*100-min(BMs$Productivity))*100)
leg[1]=1
colleg=rainbow(118)[leg] # 7 tonnes/ha would have been number 118 (calculated with linear model given that 6.47=100)

# create dataset for plotting
DAT=data.frame(loc=BMs$Roadverge,Biomass_relative_jun,Biomass_relative_aug,Mow=BMs$Mow,col=BMs$col,Prod=BMs$Productivity)
DAT$Mow_number=rep(c(1,5,3,4,6,2),each=10)
DATag=aggregate(DAT[,2:3],list(Mow=DAT$Mow,Mow_number=DAT$Mow_number,Prod=DAT$Prod<3.5),FUN=mean,na.rm=T)

if(option=='relative'){
  png(paste('relative_biomass.png'),800,1100)
}else{
  png(paste('absolute_biomass.png'),800,1100)
}

ma <- matrix(c(1,2,3,4,5,6,7,7),nrow = 4,ncol = 2,byrow = TRUE)
layout(mat = ma,heights = c(0.4,0.4,0.4,0.12))
par(mar=c(2,5,3,3))

mw=c('Aug','Nov','JunhAug','JunhNov','JunAug','JunNov')

if(option=='relative'){
  R=c(-100,100)
}else{
  R=c(0,9)
}

for(j in 1:6){
  
  DATs=DAT[DAT$Mow_number==j,]
  
  U=unique(DATs$loc)
  
  for(i in 1:length(U)){
    DATss=DATs[DATs$loc==U[i],]
    if(i==1){
      
      plot(c(0.8,1.2),rep(DATss[,2],2),ylim=c(R[1],R[2]),xlim=c(0.5,2.5),xlab='',ylab='',type='l',col=DATss$col,xaxt='n',cex.axis=1.5,cex.lab=1.5,cex.main=2,lwd=2,main=mw[j])
      
      points(c(1.8,2.2),rep(DATss[,3],2),type='l',col=DATss$col,lwd=2)
      
      
      axis(1,1:2,labels=c('June cut','Late-August cut'),cex.axis=1.5)
    }else{
      points(c(0.8,1.2),rep(DATss[,2],2),type='l',col=DATss$col,lwd=2)
      
      points(c(1.8,2.2),rep(DATss[,3],2),type='l',col=DATss$col,lwd=2)
    }
  }
  abline(h=0,lwd=2,col='black')
  grid()
  
  points(c(0.8,1.2),rep(DATag[DATag$Prod==F&DATag$Mow_number==j,4],2),lwd=4,type='l',col='blue',lty=3)
  points(c(1.8,2.2),rep(DATag[DATag$Prod==F&DATag$Mow_number==j,5],2),lwd=4,type='l',col='blue',lty=3)
  
  points(c(0.8,1.2),rep(DATag[DATag$Prod==T&DATag$Mow_number==j,4],2),lwd=4,type='l',col='orange',lty=3)
  points(c(1.8,2.2),rep(DATag[DATag$Prod==T&DATag$Mow_number==j,5],2),lwd=4,type='l',col='orange',lty=3)
  
  
}

mtext("Mowing round", side=1, outer=TRUE, line=-1,cex=1.3)

if(option=='relative'){
  mtext("Biomass (%) relative to Aug", side=2, outer=TRUE, line=-1.5,cex=1.3)
}else{
  mtext("Biomass (ton/ha)", side=2, outer=TRUE, line=-1.5,cex=1.3)
}

legend_order =t(matrix(1:14,ncol=2))

plot(1, type = "n", axes=FALSE, xlab="", ylab="")
plot_colors <-c(colleg,'orange','blue','white')
legend(x = "top",inset = 0,
       legend = c(paste(c(1:7),'ton/ha'),"LP","HP",rep("",5))[legend_order],col=c(plot_colors,rep('white',5))[legend_order],lty=c(rep(1,7),2,2,rep(0,5))[legend_order],lwd=2, cex=1.8,pt.cex = 2, bty = "n",ncol=7)


dev.off()


# vegetation univariate analyses ------------------------------------------


# set directory
if(require(rstudioapi)==0){
  install.packages('rstudioapi')
}

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# load packages
library(readxl)
library(DHARMa)
library(emmeans)
library(gridExtra)
library(vegan)
library(stringdist)
library(visreg)
library(glmmTMB)

# load data
data=read_xlsx("Vegetation surveys.xlsx")
data2=data # duplicate dataset
species_chars=read.csv2('Species_characteristics.csv')

# process data
data$Mow=data$Mowing_treatment
data$Productivity=as.numeric(scale(data$Productivity))
data[is.na(data)]=0
data$Yearsc=data$Year-mean(2021:2024) # centered year variable

# prepare plotting
f=c('gaussian','gaussian','gaussian','gaussian','poisson') # distribution to be used
mn=c('Species richness','Shannon diversity','Evenness','Characteristic species 16B','Characteristic species 14')

mn2=c('Species richness','Shannon diversity','Evenness',expression(italic("Arrhenatherion elatioris")),expression(italic("Koelerio-Corynephoretea")))

lwd=c(4,4,4,4,2) # significance of tests
lty=c(1,1,1,1,2)

png('Indices_trends.png',1000,500)

ma <- matrix(c(1,2,3,4,5,6,6,6,6,6),nrow = 2,ncol = 5,byrow = TRUE)
layout(mat = ma,heights = c(0.4,0.06))
par(mar=c(0,5,3,3))

yl=c('Species richness change per year compared to the control treatment (Aug)','Shannon diversity change per year compared to the control treatment (Aug)','Evenness change per year compared to the control treatment (Aug)','Species richness change per year compared to the control treatment (Aug)','Species richness change per year compared to the control treatment (Aug)')

R=data.frame(x=c(-2,-0.2,-0.05,-2,-2),y=c(-2,-0.2,-0.05,-2,-2)*-1) # ranges

# create colors
cl=palette.colors(palette = "Okabe-Ito")
clss=c(cl[7],cl[6],cl[4],cl[5],cl[3],cl[2])
cl=clss[2:6]

# anova tests, calculations for plots and plotting.
for(gg in 1:5){
  
  if(gg==1){
    data$nspecies=specnumber(data2[,-c(1:7)])
  }else if (gg==2){
    data$nspecies= diversity(data2[,-c(1:7)])
  }else if (gg==3){
    data$nspecies= diversity(data2[,-c(1:7)])/log(specnumber(data2[,-c(1:7)]))
  }else if (gg==4){
    Match_apr=amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)
    sel=species_chars$Arrhenatherion_elatioris[amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)]
    sels=((sel!=''))&!is.na(sel)
    data$nspecies= specnumber(data2[,sels])
  }else{
    Match_apr=amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)
    sel=species_chars$Koelerio_Corynephoretea[amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)]
    sels=((sel!=''))&!is.na(sel)
    data$nspecies= specnumber(data2[,sels])
  }
  
  
  LMERf=glmmTMB(nspecies ~ Yearsc*Mow*Productivity + (1 | Location/Block/Plot),data=data,REML=F,na.action='na.fail',family=f[gg])
  LMER2=glmmTMB(nspecies ~ Yearsc * Mow+Mow* Productivity+Yearsc * Productivity + (1 | Location/Block/Plot),data=data,REML=F,family=f[gg]) # mow 2 very significant.
  
  tA=anova(LMERf,LMER2)
  df1=data.frame(Test_for_variable="Mow x Productivity x Year",gg=mn[gg],chi=tA$Chisq[2],df=tA$`Chi Df`[2],p=tA$`Pr(>Chisq)`[2])
  
  LMERf=glmmTMB(nspecies ~ Yearsc*Productivity+Mow*Yearsc+Productivity*Yearsc + (1 | Location/Block/Plot),data=data,REML=F,na.action='na.fail',family=f[gg])
  LMER2=glmmTMB(nspecies ~ Yearsc*Productivity+Mow+Yearsc+Productivity*Yearsc+ (1 | Location/Block/Plot),data=data,REML=F,na.action='na.fail',family=f[gg])
  
  tB=anova(LMERf,LMER2)
  df2=data.frame(Test_for_variable="Mow x Year",gg=mn[gg],chi=tB$Chisq[2],df=tB$`Chi Df`[2],p=tB$`Pr(>Chisq)`[2])
  
  df=rbind(df1,df2)
  
  if(gg==1){
    DFp=df
  }else{
    DFp=rbind(DFp,df)
  }
  
  LMER=glmmTMB(nspecies ~ Yearsc*Mow*Productivity + (1 | Location/Block/Plot),data=data,na.action='na.fail',family=f[gg])  # all acceptable models according to tests plot (simulateResiduals (LMER))
  P=seq(-1.22,1.69,length.out=7)
  
  for(i in 1:length(P)){
    emtc=emtrends(LMER, pairwise ~ Mow, var = "Yearsc",adjust='none',at = list(Productivity = c(P[i])),regrid = "response") # 1 tonnes/ha
    out=emmeans::contrast(emtc, list("Treatment JunAug vs Aug" = c(-1, 1,0,0,0,0),"Treatment JunhAug vs Aug"=c(-1,0,1,0,0,0),"Treatment JunhNov vs Aug" = c(-1, 0,0,1,0,0),"Treatment JunNov vs Aug"=c(-1,0,0,0,1,0),"Treatment Nov vs Aug" = c(-1, 0,0,0,0,1)))
    outdf=data.frame(i,out)
    if(i==1){
      outdfop=outdf
    }else{
      outdfop=rbind(outdfop,outdf)
    }
    
  }
  
  u=unique(outdfop$contrast)
  
  for (j in 1:6){
    x=outdfop$i[outdfop$contrast==u[j]]
    y=outdfop$estimate[outdfop$contrast==u[j]]
    if(j==1){
      plot(x,y,col=cl[1],type='l',ylim=c(R$x[gg],R$y[gg]),lwd=lwd[gg],xlab='',ylab=yl[gg],main=mn2[gg],cex.main=1.7,cex.axis=1.5,cex.lab=1.5,lty=lty[gg])
    }else{
      points(x,y,col=cl[j],type='l',lwd=lwd[gg],lty=lty[gg])
    }
  }
  
  points(c(1,7),c(0,0),col=clss[1],lwd=lwd[gg],type='l',lty=lty[gg])
}



mtext("Productivity (tonnes/ha)", side=1, outer=TRUE, line=-1,cex=1.3)

plot(1, type = "n", axes=FALSE, xlab="", ylab="")
cl=palette.colors(palette = "Okabe-Ito")
clss=c(cl[7],cl[2],cl[4],cl[5],cl[6],cl[3])
plot_colors <-clss
legend(x = "top",inset = 0,
       legend = c("Aug", "Nov", "JunhAug","JunhNov", "JunAug",'JunNov'),col=plot_colors, lwd=3, cex=1.5,pt.cex = 2, horiz = TRUE, bty = "n")

dev.off()


outcomes_anovatests=DFp



## vegetation plotting underlying data to confirm model outcomes

# first make two choices of id and option
id=1 # select one of the following indices (choose a number from 1-5)
inds=c('nspecies','Shannon','Evenness','C16B','C14') # C16B = number of species of Arrhenatherion_elatioris, C14= number of species of Koelerio_Corynephoretea

# also choose
option='relative'

#calculate indices
data$nspecies=specnumber(data2[,-c(1:7)])
data$Shannon=diversity(data2[,-c(1:7)])
data$Evenness=diversity(data2[,-c(1:7)])/log(specnumber(data2[,-c(1:7)]))

Match_apr=amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)
sel=species_chars$Arrhenatherion_elatioris[amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)]
sels=((sel!=''))&!is.na(sel)
data$C16B= specnumber(data2[,sels])

Match_apr=amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)
sel=species_chars$Koelerio_Corynephoretea[amatch(colnames(data2), species_chars$Scientific_name,maxDist=2)]
sels=((sel!=''))&!is.na(sel)
data$C14= specnumber(data2[,sels])

# select selected index
data=data.frame(data)
data$ind=data[,inds[id]]

# create colors for plot based on road verge productivity
rd=round((data2$Productivity-min(data2$Productivity))/max(data2$Productivity-min(data2$Productivity))*100)
rd[rd==0]=1
data$col= rainbow(130)[rd]

# create legend colors for 1-7 ton/ha.
leg=round((c(1:7)*100-min(data2$Productivity))/max(c(1:7)*100-min(data2$Productivity))*100)
leg[1]=1
colleg=rainbow(118)[leg]

# ylabs of plot
if(option=='relative'){
  yl=c('Species richness change compared to 2021','Shannon diversity change compared to 2021','Evenness change compared to 2021','Species richness change compared to 2021','Species richness change compared to 2021')
}else{
  yl=c('Species richness','Shannon diversity','Evenness','Species richness','Species richness')
}

if(option=='relative'){
  data$ind[data$Year==2022]=data$ind[data$Year==2022]-data$ind[data$Year==2021]
  data$ind[data$Year==2023]=data$ind[data$Year==2023]-data$ind[data$Year==2021]
  data$ind[data$Year==2024]=data$ind[data$Year==2024]-data$ind[data$Year==2021]
  data$ind[data$Year==2021]=data$ind[data$Year==2021]-data$ind[data$Year==2021]
}

# aggregate data per road verge per mowing treatment per year (over three replicates)
data_ag=aggregate(list(ind=data$ind),list(Mowing_treatment=data$Mowing_treatment,Year=data$Year,Location=data$Location,col=data$col),FUN=mean)

# reshape(data_ag,direction = "wide",v.names  = "ind",idvar = c("Mowing_treatment",    "Location",     "col" ),timevar = "Year")

data_agcs=aggregate(list(ind=data$ind),list(Mowing_treatment=data$Mowing_treatment,Year=data$Year,Prod=data2$Productivity<350),FUN=mean)

if(option=='relative'){
  png(paste('Relative_data_',inds[id],'.png'),800,1100)
}else{
  png(paste('Absolute_data_',inds[id],'.png'),800,1100)
}

ma <- matrix(c(1,2,3,4,5,6,7,7),nrow = 4,ncol = 2,byrow = TRUE)
layout(mat = ma,heights = c(0.4,0.4,0.4,0.12))
par(mar=c(2,5,3,3))

if(option=='relative'){
  if(id!=3){
    R=range(data_ag$ind)
    MR=max(abs(R))
    R=c(-ceiling(MR),ceiling(MR))
  }else{
    R=range(data_ag$ind)
    MR=max(abs(R))
    R=c(-ceiling(MR*10),ceiling(MR*10))/10
  }
}else{
  R=range(data_ag$ind)
}

treats=c('Aug','Nov','JunhAug','JunhNov','JunAug','JunNov')
for(j in 1:6){
  
  data_agd=data_ag[data_ag$Mowing_treatment==treats[j],]
  U=unique(data_agd$Location)
  
  for(i in 1:length(U)){
    data_agds=data_agd[data_agd$Location==U[i],]
    if(i==1){
      plot(data_agds$Year,data_agds$ind,ylim=c(R[1],R[2]),xlab='',ylab='',type='l',col=data_agds$col,main=treats[j],xaxt='n',cex.axis=1.5,cex.lab=1.5,cex.main=2,lwd=2)
      axis(1,2021:2024,labels=2021:2024,cex.axis=1.5)
    }else{
      points(data_agds$Year,data_agds$ind,type='l',col=data_agds$col,lwd=2)
    }
  }
  abline(h=0,lwd=2,col='black')
  grid()
  
  points(data_agcs[data_agcs$Prod==F&data_agcs$Mowing_treatment==treats[j],"Year"],data_agcs[data_agcs$Prod==F&data_agcs$Mowing_treatment==treats[j],"ind"],lwd=4,type='l',col='blue',lty=3)
  points(data_agcs[data_agcs$Prod==T&data_agcs$Mowing_treatment==treats[j],"Year"],data_agcs[data_agcs$Prod==T&data_agcs$Mowing_treatment==treats[j],"ind"],lwd=4,type='l',col='orange',lty=3)
  
}

mtext("Year", side=1, outer=TRUE, line=-1,cex=1.3)
mtext(yl[id], side=2, outer=TRUE, line=-1.5,cex=1.3)

legend_order =t(matrix(1:14,ncol=2))

plot(1, type = "n", axes=FALSE, xlab="", ylab="")
plot_colors <-c(colleg,'orange','blue','white')
legend(x = "top",inset = 0,
       legend = c(paste(c(1:7),'ton/ha'),"LP","HP",rep("",5))[legend_order],col=c(plot_colors,rep('white',5))[legend_order],lty=c(rep(1,7),2,2,rep(0,5))[legend_order],lwd=2, cex=1.8,pt.cex = 2, bty = "n",ncol=7)


dev.off()

# vegetation multivariate analyses ------------------------------------------

# set directory
if(require(rstudioapi)==0){
  install.packages('rstudioapi')
}

setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

library(readxl)
library(ggplot2)
library(gridExtra)
library(cowplot)
library(vegan)
library(ggrepel)
library(stringdist)
library(car)
library(dplyr)

# load data
data=read_xlsx("Vegetation surveys.xlsx")
data2=data # duplicate dataset
groups=read.csv2('Species_characteristics.csv')

specs=data[,-c(1:7)]

# group covers
g=groups$Group[amatch(colnames(specs), groups$Scientific_name,maxDist=2)]
group_cov=t(aggregate(t(specs),list(g),FUN=sum)[,-1])
group_cov=data.frame(group_cov)
colnames(group_cov)=aggregate(t(specs),list(g),FUN=sum)[,1]

# grass:forbratio
h=groups$GrasorForb[amatch(colnames(specs), groups$Scientific_name,maxDist=2)]
gf=t(aggregate(t(specs),list(h),FUN=sum)[,-1])
colnames(gf)=aggregate(t(specs),list(h),FUN=sum)[,1]
grass_forbratio=gf[,2]/ (  gf[,1]+gf[,2])

# CSR
csr=groups$CSR[amatch(colnames(specs), groups$Scientific_name,maxDist=2)]
C=rep(0,length(csr)); C[csr=='cs']=0.5;C[csr=='cr']=0.5;C[csr=='csr']=1/3;C[csr=='c']=1;C[csr=='#N/A']=NA
S=rep(0,length(csr)); S[csr=='cs']=0.5;S[csr=='sr']=0.5;S[csr=='csr']=1/3;S[csr=='s']=1;S[csr=='#N/A']=NA
R=1-C-S

C_sum=(specs>0)*t(replicate(dim(specs)[1], C))
S_sum=(specs>0)*t(replicate(dim(specs)[1], S))
R_sum=(specs>0)*t(replicate(dim(specs)[1], R))

csr_data=data.frame(C=apply(C_sum,1,sum,na.rm=T)/specnumber(specs),S=apply(S_sum,1,sum,na.rm=T)/specnumber(specs),R=apply(R_sum,1,sum,na.rm=T)/specnumber(specs))

# indices
groups$Height_adj[groups$GrasorForb=='Neither']=NA
hh=as.numeric(groups$Height_adj[amatch(colnames(specs), groups$Scientific_name,maxDist=2)])
height=apply((specs>0)*t(replicate(dim(specs)[1], hh)),1,sum,na.rm=T)/specnumber(specs[,!is.na(hh)])

ll=as.numeric(groups$Lifespan_number[amatch(colnames(specs), groups$Scientific_name,maxDist=2)])
ls=apply((specs>0)*t(replicate(dim(specs)[1], ll)),1,sum,na.rm=T)/specnumber(specs[,!is.na(ll)])

ellenberg=read.csv2('Ellenberg_values.csv')

DFind=data.frame(ellenberg[,-c(1:7,8,14,16)],height,lifespan=ls)
colnames(DFind)=c('Light','Mowing','N','Temp','Moist','pH','Height','LifeSpan')
DFind[,]=apply(DFind,2,as.numeric)

# datatransformations
# species
specs_T=specs/100
specs_T=car::logit(specs_T,percents=F,0.025) # logit data transformation
# species group overs
group_cov_T=group_cov/100
APLL=apply(group_cov_T,2,max)
group_cov_T[,APLL>1]=group_cov_T[,APLL>1]/t(replicate(dim(group_cov)[1],APLL[APLL>1])) # if max cover >100, divide by that instead
group_cov_T=car::logit(group_cov_T,percents=F,0.025) # logit data transformation
group_cov_T$Grass.Forb=grass_forbratio

# convert to trends:
# function to calculate coefficients per plot
lm2=function(x,y){
  y[is.na(y)]=0
  S=summary(lm(y~x))
  S$coefficients[2,1]
}

# species group cover
group_cov_Tdf=data.frame(Year=data$Year,Plot=data$Plot,Location=data$Location, group_cov_T)

for(i in 1:dim(group_cov_T)[2]){
  AG_lm2=eval(parse(text=paste("group_cov_Tdf %>% group_by(Plot,Location) %>% summarize(lm2(Year," ,colnames(group_cov_Tdf)[i+3], "))",sep="")))
  DF=data.frame(X=as.data.frame(AG_lm2[,3]))
  if(i==1){
    DFop=DF
  }else{
    DFop=cbind(DFop,DF)
  }
}
colnames(DFop)=colnames(group_cov_T)
group_cov_trend=DFop


# species cover
specs_Ts=specs_T[,apply(specs>0,2,sum)>=20] #subset species with at least 20 recordings
lowprod20rec=data.frame(species=colnames(specs),N20=apply(specs[data$Productivity<400, ]>0,2,sum)>=20,group=g); lowprod20rec=lowprod20rec[apply(specs>0,2,sum)>=20,]
highprod20rec=data.frame(species=colnames(specs),N20=apply(specs[data$Productivity>400, ]>0,2,sum)>=20,group=g);highprod20rec=highprod20rec[apply(specs>0,2,sum)>=20,]
specs_Tdf=data.frame(Year=data$Year,Plot=data$Plot,Location=data$Location, specs_Ts)

for(i in 1:dim(specs_Ts)[2]){
  AG_lm2=eval(parse(text=paste("specs_Tdf %>% group_by(Plot,Location) %>% summarize(lm2(Year," ,colnames(specs_Tdf)[i+3], "))",sep="")))
  DF=data.frame(X=as.data.frame(AG_lm2[,3]))
  if(i==1){
    DFop=DF
  }else{
    DFop=cbind(DFop,DF)
  }
}
colnames(DFop)=colnames(specs_Ts)
specs_trend=DFop

# abbreviat species names for clearer plotting
for(i in 1:dim(specs_trend)[2]){
  nm=paste(substr(strsplit(colnames(specs_trend), "[.]")[[i]][1],1,1),strsplit(colnames(specs_trend), "[.]")[[i]][2],sep='.')
  if(i==1){
    nmop=nm
  }else{
    nmop=c(nmop,nm)
  }
}
colnames(specs_trend)=nmop

# csr
csr_data_df=data.frame(Year=data$Year,Plot=data$Plot,Location=data$Location, csr_data)

for(i in 1:dim(csr_data)[2]){
  AG_lm2=eval(parse(text=paste("csr_data_df %>% group_by(Plot,Location) %>% summarize(lm2(Year," ,colnames(csr_data_df)[i+3], "))",sep="")))
  DF=data.frame(X=as.data.frame(AG_lm2[,3]))
  if(i==1){
    DFop=DF
  }else{
    DFop=cbind(DFop,DF)
  }
}
colnames(DFop)=colnames(csr_data)
csr_trend=DFop


# indices
DFind_df=data.frame(Year=data$Year,Plot=data$Plot,Location=data$Location, DFind)

for(i in 1:dim(DFind)[2]){
  AG_lm2=eval(parse(text=paste("DFind_df %>% group_by(Plot,Location) %>% summarize(lm2(Year," ,colnames(DFind_df)[i+3], "))",sep="")))
  DF=data.frame(X=as.data.frame(AG_lm2[,3]))
  if(i==1){
    DFop=DF
  }else{
    DFop=cbind(DFop,DF)
  }
}
colnames(DFop)=colnames(DFind)
inds_trend=DFop



## testing interactive effect of Mow x Productivity on the trends
D=data[data$Year==2021,];D=D[order(D$Plot,D$Location),]

Mow=D$Mowing_treatment
Mow=data.frame(Mow,Location=D$Location,Prod=as.numeric(scale(D$Productivity)))
specs_trend[,]=scale(specs_trend)

RDA=rda(specs_trend~Mow*Prod+Condition(Location),data=Mow)
RDA0=rda(specs_trend~Mow+Prod+Condition(Location),data=Mow)
C1=anova(RDA,RDA0)

RDAStats1=data.frame(comparison="Mowing treatment x productivity",index="Species",F_value=C1$F[2],p_value=C1$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))

group_cov_trend[,]=scale(group_cov_trend)
RDA=rda(group_cov_trend~Mow*Prod+Condition(Location),data=Mow)
RDA0=rda(group_cov_trend~Mow+Prod+Condition(Location),data=Mow)
C2=anova(RDA,RDA0)

RDAStats2=data.frame(comparison="Mowing treatment x productivity",index="Species groups",F_value=C2$F[2],p_value=C2$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))

csr_trend[,]=scale(csr_trend)
RDA=rda(csr_trend~Mow*Prod+Condition(Location),data=Mow)
RDA0=rda(csr_trend~Mow+Prod+Condition(Location),data=Mow)
C3=anova(RDA,RDA0)

RDAStats3=data.frame(comparison="Mowing treatment x productivity",index="csr",F_value=C3$F[2],p_value=C3$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))

inds_trend[,]=scale(inds_trend)
RDA=rda(inds_trend~Mow*Prod+Condition(Location),data=Mow)
RDA0=rda(inds_trend~Mow+Prod+Condition(Location),data=Mow)
C4=anova(RDA,RDA0)

RDAStats4=data.frame(comparison="Mowing treatment x productivity",index="Env-indices",F_value=C4$F[2],p_value=C4$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))

# because species and species group cover RDAs showed interactive effects, we calculated results for low and high productive locations separately.

group_cov_trend_low=group_cov_trend[Mow$Prod <0,]
group_cov_trend_low[,]=scale(group_cov_trend_low)
Mow_low=Mow[Mow$Prod<0,]
RDAgrouplow=rda(group_cov_trend_low~ Mow+Condition(Location),data=Mow_low)
RDA0=rda(group_cov_trend_low~ 1+Condition(Location),data=Mow_low)
C5=anova(RDAgrouplow,RDA0) 

RDA=RDAgrouplow
RDAStats5=data.frame(comparison="Mowing treatment",index="Species groups low productivity",F_value=C5$F[2],p_value=C5$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


group_cov_trend_high=group_cov_trend[Mow$Prod >0,]
group_cov_trend_high[,]=scale(group_cov_trend_high)
Mow_high=Mow[Mow$Prod>0,]
RDAgrouphigh=rda(group_cov_trend_high~ Mow+Condition(Location),data=Mow_high)
RDA0=rda(group_cov_trend_high~ 1+Condition(Location),data=Mow_high)
C6=anova(RDAgrouphigh,RDA0) 

RDA=RDAgrouphigh
RDAStats6=data.frame(comparison="Mowing treatment",index="Species groups high productivity",F_value=C6$F[2],p_value=C6$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


spec_cov_trend_low=specs_trend[Mow$Prod <0,lowprod20rec$N20]
spec_cov_trend_low[,]=scale(spec_cov_trend_low)
Mow_low=Mow[Mow$Prod<0,]
RDAspeclow=rda(spec_cov_trend_low~ Mow+Condition(Location),data=Mow_low)
RDA0=rda(spec_cov_trend_low~ 1+Condition(Location),data=Mow_low)
C7=anova(RDAspeclow,RDA0) 

RDA=RDAspeclow
RDAStats7=data.frame(comparison="Mowing treatment",index="Species low productivity",F_value=C7$F[2],p_value=C7$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


spec_cov_trend_high=specs_trend[Mow$Prod >0,highprod20rec$N20]
spec_cov_trend_high[,]=scale(spec_cov_trend_high)
Mow_high=Mow[Mow$Prod>0,]
RDAspechigh=rda(spec_cov_trend_high~ Mow+Condition(Location),data=Mow_high)
RDA0=rda(spec_cov_trend_high~ 1+Condition(Location),data=Mow_high)
C8=anova(RDAspechigh,RDA0) 

RDA=RDAspechigh
RDAStats8=data.frame(comparison="Mowing treatment",index="Species high productivity",F_value=C8$F[2],p_value=C8$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


# for csr and environmental indices/species traits, no such interaction was found, so we can evaluate the effect of Mow on the whole dataset.
RDAcsr=rda(csr_trend~ Mow+Condition(Location),data=Mow)
RDA0=rda(csr_trend~1+Condition(Location),data=Mow)
C9=anova(RDAcsr,RDA0) 

RDA=RDAcsr
RDAStats9=data.frame(comparison="Mowing treatment",index="csr",F_value=C9$F[2],p_value=C9$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


RDAind=rda(inds_trend~ Mow+Condition(Location),data=Mow)
RDA0=rda(inds_trend~1+Condition(Location),data=Mow)
C10=anova(RDAind,RDA0) 

RDA=RDAind
RDAStats10=data.frame(comparison="Mowing treatment",index="Env-indices",F_value=C10$F[2],p_value=C10$`Pr(>F)`[2],Explvar_full=sum(RDA$CCA$eig) / RDA$tot.chi,perc.ax12_full=sum(RDA$CCA$eig[1:2])/sum(RDA$CCA$eig))


RDAstats=rbind(RDAStats1,RDAStats2,RDAStats3,RDAStats4,RDAStats5,RDAStats6,RDAStats7,RDAStats8,RDAStats9,RDAStats10)
write.csv(RDAstats,'RDAstats.csv')


# PCA alternatives for RDAs presented in the main part of the paper

group_cov_trend_low[,]=scale(group_cov_trend_low)
PCA_cov_low=rda(group_cov_trend_low,data=Mow_low,na.action=na.exclude)
Explvarsel=(Mow_low[,c('Mow')])
data=model.matrix(~ as.factor(Mow) - 1, data = Mow_low)
colnames(data)=c('Aug','JunAug','JunhAug','JunhNov','JunNov','Nov')
EV_cov_low=envfit(PCA_cov_low,data,choices=c(1,2,3))

group_cov_trend_high[,]=scale(group_cov_trend_high)
PCA_cov_high=rda(group_cov_trend_high,data=Mow_high,na.action=na.exclude)
Explvarsel=(Mow_high[,c('Mow')])
data=model.matrix(~ as.factor(Mow) - 1, data = Mow_high)
colnames(data)=c('Aug','JunAug','JunhAug','JunhNov','JunNov','Nov')
EV_cov_high=envfit(PCA_cov_high,data,choices=c(1,2,3))

PCA_ind=rda(inds_trend,data=Mow,na.action=na.exclude)
Explvarsel=(Mow[,c('Mow')])
data=model.matrix(~ as.factor(Mow) - 1, data = Mow)
colnames(data)=c('Aug','JunAug','JunhAug','JunhNov','JunNov','Nov')
EV_ind=envfit(PCA_ind,data,choices=c(1,2,3))


# function for plotting result of group cover, indices and csr
Mod_plotter=function(VeganOutput=RDA,RDA1='RDA1',RDA2='RDA2',Sig=1,EV=1){
  
  x=data.frame(vegan::scores(summary(VeganOutput),display="species"))*10
  x$species=row.names(x)
  
  if(length(EV)==1){
    y=data.frame(VeganOutput$CCA$centroids)
  }else{
    y=vegan::scores(EV,display="vectors")
    y=as.data.frame(y)
  }
  
  y$AbioticParameter=row.names(y)
  
  y$x1=0
  y$y1=0
  
  ysig=y
  ysig$AbioticParameter=paste(y$AbioticParameter,'',sep='')
  
  G=rep(1,dim(x)[1])*4
  goodnessdist=rep(1,dim(x)[1])*4
  
  if(dim(y)[1]==1&length(EV)==1){
    x$RDA2=rep(0,length(x$RDA1))
  }
  
  p <- eval(parse(text=paste("ggplot(x, aes(",RDA1,",", RDA2,")) +geom_point(color =\"red\")")))
  groups=''
  
  if(dim(y)[1]>1){
    fact=diff(range(x[,1]))/pmax(max(abs(y[,1])),max(abs(y[,1])))/2
    YR=as.numeric(t(apply(y,2,range)[1,]))-as.numeric(t(apply(y,2,range)[2,]))
    y[,!is.na(YR)]=y[,!is.na(YR)]*fact
  }else{
    fact=diff(range(x[,1]))/diff(range(c(1,0)))/1.5
    YR=c(0,fact)
    y[1,1]=fact
    y$RDA2=0
  }
  y$AbioticParameter=gsub('Mow','',y$AbioticParameter)
  
  f=1.5
  p3=eval(parse(text=paste("p3 =p+ geom_segment(aes(x =x1 , y = y1, xend =" ,RDA1,", yend =" ,RDA2,"), data = y,size = 1*f, arrow = arrow(length = unit(0.03, \"npc\")),colour =\"black\")")))
  
  y$species=y$AbioticParameter
  IS=intersect(colnames(y),colnames(x))
  x2=x[,is.element(colnames(x),IS)]
  if(groups==''){
    x2$col='black'
  }else{
    x2$col=cg$col[match(groups,cg$group)]
  }
  y2=y[,is.element(colnames(y),IS)]
  y2$col='blue'
  
  z2=rbind(x2,y2)
  if(dim(y)[1]==1){
    z2$RDA2=rep(0,dim(z2)[1])
  }
  if(is.numeric(z2[,2])){
    if(diff(range(z2[,2]))/diff(range(z2[,1]))<1.3){
      f2=1.3
    }else{
      f2=diff(range(z2[,2]))/diff(range(z2[,1]))+0.2
    }
  }else{
    f2=1.3
  }
  Rr=range(z2[,1])*f2
  Rr[1]=(range(z2[,1])*f2)[2]-diff(range(z2[,1]))*f2
  Rr2=Rr
  if(length(EV)!=1){
    Rr2[1]=range(diff(Rr)/diff(range(z2[,'PC2']))*z2[,'PC2'])[1]
    Rr2[2]=range(diff(Rr)/diff(range(z2[,'PC2']))*z2[,'PC2'])[2]
  }else{
    Rr2[1]=range(diff(Rr)/diff(range(z2[,RDA2]))*z2[,RDA2])[1]
    Rr2[2]=range(diff(Rr)/diff(range(z2[,RDA2]))*z2[,RDA2])[2]
  }
  p4=p3+theme_bw() +  
    theme(legend.position="none") +
    theme(panel.grid.minor = element_blank(), panel.grid.major =   element_blank())
  
  if(Sig==1){
    z2$species[ match(y$species,z2$species)]=ysig$AbioticParameter
  }
  els=gsub('Mowing','',z2$species)==z2$species
  z2$species[els]=gsub('Mow','',z2$species[els])
  
  p4=eval(parse(text=paste("p4+geom_text_repel(data=z2,aes(x=",RDA1,", y=",RDA2,",  label = species),max.overlaps = Inf,size=c(G,rep(6,dim(y2)[1]))*1.5*f,force=50,colour=z2$col)")))
  
  
  p4=p4+theme(axis.text=element_text(size=24*f))+ ylim(Rr2[1], Rr2[2])+xlim(Rr[1], Rr[2])+theme(axis.title=element_text(size=24*f))
  p4=p4+theme(axis.text.y = element_text( angle=90))
}


Mod_plotter2=function(VeganOutput=RDA,RDA1='RDA1',RDA2='RDA2',Sig=1,EV=1,cols=RB){# function for species covers
  x=data.frame(vegan::scores(summary(VeganOutput),display="species"))*10
  x$species=row.names(x)
  
  if(length(EV)==1){
    y=data.frame(VeganOutput$CCA$centroids)
  }else{
    y=vegan::scores(EV,display="vectors")
    y=as.data.frame(y)
  }
  
  y$AbioticParameter=row.names(y)
  
  y$x1=0
  y$y1=0
  
  ysig=y
  ysig$AbioticParameter=paste(y$AbioticParameter,'',sep='')
  
  G=rep(1,dim(x)[1])*4
  goodnessdist=rep(1,dim(x)[1])*4
  
  if(dim(y)[1]==1&length(EV)==1){
    x$RDA2=rep(0,length(x$RDA1))
  }
  
  p <- eval(parse(text=paste("ggplot(x, aes(",RDA1,",", RDA2,")) +geom_point(color =cols)")))
  
  groups=''
  
  if(dim(y)[1]>1){
    fact=diff(range(x[,1]))/pmax(max(abs(y[,1])),max(abs(y[,1])))/2
    YR=as.numeric(t(apply(y,2,range)[1,]))-as.numeric(t(apply(y,2,range)[2,]))
    y[,!is.na(YR)]=y[,!is.na(YR)]*fact
  }else{
    fact=diff(range(x[,1]))/diff(range(c(1,0)))/1.5
    YR=c(0,fact)
    y[1,1]=fact
    y$RDA2=0
  }
  y$AbioticParameter=gsub('Mow','',y$AbioticParameter)
  
  f=1.5
  p3=eval(parse(text=paste("p3 =p+ geom_segment(aes(x =x1 , y = y1, xend =" ,RDA1,", yend =" ,RDA2,"), data = y,size = 1*f, arrow = arrow(length = unit(0.03, \"npc\")),colour =\"black\")")))
  
  y$species=y$AbioticParameter
  IS=intersect(colnames(y),colnames(x))
  x2=x[,is.element(colnames(x),IS)]
  if(length(cols)<2){
    x2$col='black'
  }else{
    x2$col=cols
  }
  y2=y[,is.element(colnames(y),IS)]
  if(length(cols)<2){
    y2$col='blue'
  }else{
    y2$col='black'
    
  }
  z2=rbind(x2,y2)
  if(dim(y)[1]==1){
    z2$RDA2=rep(0,dim(z2)[1])
  }
  if(is.numeric(z2[,2])){
    if(diff(range(z2[,2]))/diff(range(z2[,1]))<1.3){
      f2=1.3
    }else{
      f2=diff(range(z2[,2]))/diff(range(z2[,1]))+0.2
    }
  }else{
    f2=1.3
  }
  Rr=range(z2[,1])*f2
  Rr[1]=(range(z2[,1])*f2)[2]-diff(range(z2[,1]))*f2
  Rr2=Rr
  if(length(EV)!=1){
    Rr2[1]=range(diff(Rr)/diff(range(z2[,'PC2']))*z2[,'PC2'])[1]
    Rr2[2]=range(diff(Rr)/diff(range(z2[,'PC2']))*z2[,'PC2'])[2]
  }else{
    Rr2[1]=range(diff(Rr)/diff(range(z2[,RDA2]))*z2[,RDA2])[1]
    Rr2[2]=range(diff(Rr)/diff(range(z2[,RDA2]))*z2[,RDA2])[2]
  }
  p4=p3+theme_bw() +  
    theme(legend.position="none") +
    theme(panel.grid.minor = element_blank(), panel.grid.major =   element_blank())
  
  if(Sig==1){
    z2$species[ match(y$species,z2$species)]=ysig$AbioticParameter
  }
  els=gsub('Mowing','',z2$species)==z2$species
  z2$species[els]=gsub('Mow','',z2$species[els])
  sz=c(G,rep(6,dim(y2)[1]))
  sz[sz==4]=3
  p4=eval(parse(text=paste("p4+geom_text_repel(data=z2,aes(x=",RDA1,", y=",RDA2,",  label = species),max.overlaps = Inf,size=sz*1.5*f,force=50,colour=z2$col)")))
  
  
  p4=p4+theme(axis.text=element_text(size=24*f))+ ylim(Rr2[1], Rr2[2])+xlim(Rr[1], Rr[2])+theme(axis.title=element_text(size=24*f))
  p4=p4+theme(axis.text.y = element_text( angle=90))
}



p1=Mod_plotter(VeganOutput=RDAgrouplow)
p1b=Mod_plotter(VeganOutput=PCA_cov_low,RDA1='PC1',RDA2='PC2',Sig=1,EV=EV_cov_low )

p2=Mod_plotter(VeganOutput=RDAgrouphigh)
p2b=Mod_plotter(VeganOutput=PCA_cov_high,RDA1='PC1',RDA2='PC2',Sig=1,EV=EV_cov_high )

p3=Mod_plotter(VeganOutput=RDAind)
p3b=Mod_plotter(VeganOutput=PCA_ind,RDA1='PC1',RDA2='PC2',Sig=1,EV=EV_ind )

colser=c('Grass_s','Grass_t','Forb_s','Forb_t','Forb_tr','Annual','Annual_tr','Moss')
g=lowprod20rec$group[ lowprod20rec$N20]
RB=rainbow(9)[match(g,colser)]

p4=Mod_plotter2(VeganOutput=RDAspeclow)

colser=c('Grass_s','Grass_t','Forb_s','Forb_t','Forb_tr','Annual','Annual_tr','Moss')
g=highprod20rec$group[ highprod20rec$N20]
RB=rainbow(9)[match(g,colser)]

p5=Mod_plotter2(VeganOutput=RDAspechigh)

p6=Mod_plotter(VeganOutput=RDAcsr)


t=theme(axis.text.x=element_blank(),axis.ticks.x=element_blank(),axis.text.y=element_blank(),axis.ticks.y=element_blank())+ theme(plot.title = element_text(size=40))



while(length(dev.list())>0){
  dev.off()
}
WD=paste(getwd(),'/RDA_main.png',sep = '')
png(WD,1650,550)
grid.arrange(p1+t+ ggtitle("(A)"),p2+t+ ggtitle("(B)"),p3+t+ ggtitle("(C)"), ncol = 3, nrow = 1)

dev.off()

while(length(dev.list())>0){
  dev.off()
}
WD=paste(getwd(),'/PCA_suppl.png',sep = '')
png(WD,1650,550)
grid.arrange(p1b+t+ ggtitle("(A)"),p2b+t+ ggtitle("(B)"),p3b+t+ ggtitle("(C)"), ncol = 3, nrow = 1)

dev.off()


while(length(dev.list())>0){
  dev.off()
}
WD=paste(getwd(),'/RDA_species.png',sep = '')
png(WD,1500,750)

data=data.frame(x=rep(1,9),y=seq(1,9),col=rainbow(9),labs=c(colser,'shrub'))[-9,]
padd=ggplot(data, aes(x = x, y = y, label = labs)) +geom_point(aes(color = col), size = 4) +  geom_text(hjust = -0.2,size = 7) +scale_color_identity() +xlim(0.99,1.07)+ylim(-10,10)+theme_void() 

combined_plot <- plot_grid( p4+t+ ggtitle("(A)"),p5+t+ ggtitle("(B)"),padd, ncol = 3,rel_widths  = c(4, 4, 1) ) 
combined_plot
dev.off()

while(length(dev.list())>0){
  dev.off()
}
WD=paste(getwd(),'/RDA_csr.png',sep = '')
png(WD,1200,600)
grid.arrange(p6+t,p6+t, ncol = 2, nrow = 1)

dev.off()


# Option to plot vector figures

# cairo_ps("rda.eps", height = 8.125, width = 15)
# grid.arrange(...)
# dev.off()

