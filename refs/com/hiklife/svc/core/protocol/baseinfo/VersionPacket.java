/*     */ package com.hiklife.svc.core.protocol.baseinfo;
/*     */ import java.io.UnsupportedEncodingException;

import refs.com.hiklife.svc.core.protocol.InvalidRFBMessageException;
import refs.com.hiklife.svc.core.protocol.baseinfo.VersionPacket;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ public class VersionPacket
/*     */ {
/*  16 */   public static final VersionPacket VERSION_3_8 = new VersionPacket(3, 8);
/*     */ 
/*     */ 
/*     */   
/*     */   private static final int VERSION_LENGTH = 12;
/*     */ 
/*     */ 
/*     */   
/*     */   private int major;
/*     */ 
/*     */   
/*     */   private int minor;
/*     */ 
/*     */ 
/*     */   
/*     */   public VersionPacket(byte[] orgMsgBytes) throws InvalidRFBMessageException {
/*  32 */     determineVersion(orgMsgBytes);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public VersionPacket(int major, int minor) {
/*  42 */     this.major = major;
/*  43 */     this.minor = minor;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public VersionPacket(String versionString) throws InvalidRFBMessageException {
/*  53 */     parseVersion(formatVersionString(versionString));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static int[] parseVersionText(String versionText) throws InvalidRFBMessageException {
/*  64 */     if (versionText.startsWith("RFB ")) {
/*     */       try {
/*  66 */         int[] v = new int[2];
/*  67 */         v[0] = Integer.parseInt(versionText.substring(4, 7));
/*  68 */         v[1] = Integer.parseInt(versionText.substring(8, 11));
/*  69 */         return v;
/*  70 */       } catch (Exception ex) {
/*  71 */         throw new IllegalArgumentException("RFB version parsing failed");
/*     */       } 
/*     */     }
/*  74 */     throw new InvalidRFBMessageException("RFB version parsing failed");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   static String formatVersionString(String versionString) {
/*  84 */     String[] v = versionString.split("\\.");
/*  85 */     return String.format("RFB %03d.%03d\n", new Object[] { Integer.valueOf(Integer.parseInt(v[0])), Integer.valueOf(Integer.parseInt(v[1])) });
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void parseVersion(String versionText) throws InvalidRFBMessageException {
/*  95 */     int[] ident = parseVersionText(versionText);
/*  96 */     this.major = ident[0];
/*  97 */     this.minor = ident[1];
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void determineVersion(byte[] buf) throws InvalidRFBMessageException {
/*     */     String versionText;
/*     */     try {
/* 109 */       versionText = (new String(buf, 0, 12, "ASCII")).trim();
/* 110 */     } catch (UnsupportedEncodingException e) {
/* 111 */       throw new InvalidRFBMessageException("RFB version parsing failed");
/*     */     } 
/* 113 */     parseVersion(versionText);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public byte[] formatVersion() throws InvalidRFBMessageException {
/* 123 */     String sendVersion = String.format("RFB %03d.%03d\n", new Object[] { Integer.valueOf(this.major), Integer.valueOf(this.minor) });
/*     */     try {
/* 125 */       return sendVersion.getBytes("ASCII");
/* 126 */     } catch (UnsupportedEncodingException e) {
/* 127 */       throw new InvalidRFBMessageException(e.getMessage());
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getMajor() {
/* 137 */     return this.major;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setMajor(int major) {
/* 146 */     this.major = major;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public int getMinor() {
/* 155 */     return this.minor;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void setMinor(int minor) {
/* 164 */     this.minor = minor;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/baseinfo/VersionPacket.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */