/*     */ package com.cetiti.kvm.jni;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class G726State
/*     */ {
/*  26 */   private long yl = 34861L;
/*  27 */   private int yu = 544;
/*  28 */   private int dms = 0;
/*  29 */   private int dml = 0;
/*  30 */   private int ap = 0;
/*  31 */   private int[] a = new int[2];
/*  32 */   private int[] b = new int[6];
/*  33 */   private int[] sr = new int[2];
/*  34 */   private short[] dq = new short[6];
/*  35 */   private int[] pk = new int[2]; public G726State() {
/*     */     int cnta;
/*  37 */     for (cnta = 0; cnta < 2; cnta++) {
/*  38 */       this.a[cnta] = 0;
/*  39 */       this.pk[cnta] = 0;
/*  40 */       this.sr[cnta] = 32;
/*     */     } 
/*  42 */     for (cnta = 0; cnta < 6; cnta++) {
/*  43 */       this.b[cnta] = 0;
/*  44 */       this.dq[cnta] = 32;
/*     */     } 
/*  46 */     this.td = 0;
/*     */   }
/*     */ 
/*     */   
/*     */   private int td;
/*     */ 
/*     */   
/*     */   public long getYl() {
/*  54 */     return this.yl;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setYl(long yl) {
/*  62 */     this.yl = yl;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getYu() {
/*  70 */     return this.yu;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setYu(int yu) {
/*  78 */     this.yu = yu;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getDms() {
/*  86 */     return this.dms;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDms(int dms) {
/*  94 */     this.dms = dms;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getDml() {
/* 102 */     return this.dml;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDml(int dml) {
/* 110 */     this.dml = dml;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getAp() {
/* 118 */     return this.ap;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setAp(int ap) {
/* 126 */     this.ap = ap;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int[] getA() {
/* 134 */     return this.a;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setA(int[] a) {
/* 142 */     this.a = a;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int[] getB() {
/* 150 */     return this.b;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setB(int[] b) {
/* 158 */     this.b = b;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int[] getPk() {
/* 166 */     return this.pk;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setPk(int[] pk) {
/* 174 */     this.pk = pk;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public short[] getDq() {
/* 182 */     return this.dq;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setDq(short[] dq) {
/* 190 */     this.dq = dq;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int[] getSr() {
/* 198 */     return this.sr;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setSr(int[] sr) {
/* 206 */     this.sr = sr;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getTd() {
/* 214 */     return this.td;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setTd(int td) {
/* 222 */     this.td = td;
/*     */   }
/*     */ 
/*     */   
/*     */   public String toString() {
/* 227 */     return "G726State{yl=" + this.yl + ", yu=" + this.yu + ", dms=" + this.dms + ", dml=" + this.dml + ", ap=" + this.ap + ", a=" + this.a + ", b=" + this.b + ", sr=" + this.sr + ", dq=" + this.dq + ", pk=" + this.pk + '}';
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/cetiti/kvm/jni/G726State.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */