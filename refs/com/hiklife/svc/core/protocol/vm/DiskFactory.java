/*     */ package com.hiklife.svc.core.protocol.vm;
/*     */ import java.io.BufferedReader;
/*     */ import java.io.File;
/*     */ import java.io.FileReader;
/*     */ import java.io.IOException;
/*     */ import java.util.ArrayList;
/*     */ import java.util.Iterator;
/*     */ import java.util.List;
/*     */ import java.util.regex.Matcher;
/*     */ import java.util.regex.Pattern;
/*     */ import javax.swing.filechooser.FileSystemView;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.DiskMemory;
import refs.com.hiklife.svc.core.protocol.vm.DiskFactory;
import refs.com.hiklife.svc.core.protocol.vm.MediaType;
import refs.com.hiklife.svc.util.OSUtils;
/*     */ 
/*     */ 
/*     */ public class DiskFactory
/*     */ {
/*  21 */   private static final Logger log = LoggerFactory.getLogger(DiskFactory.class);
/*     */   public static List<MediaType> getLinkMedias() {
/*  23 */     if (OSUtils.isWin()) {
/*  24 */       return getWinLinkMedias();
/*     */     }
/*  26 */     return getLinuxLinkMedias();
/*     */   }
/*     */ 
/*     */   
/*     */   private static List<MediaType> getWinLinkMedias() {
/*  31 */     File[] drivers = File.listRoots();
/*  32 */     FileSystemView fileSystemView = FileSystemView.getFileSystemView();
/*  33 */     List<MediaType> mediaTypes = new ArrayList<>();
/*  34 */     for (File file : drivers) {
/*     */       
/*  36 */       String diskType = fileSystemView.getSystemTypeDescription(file);
/*  37 */       if (diskType.contains("移动") || diskType.contains("U 盘")) {
/*  38 */         MediaType mediaType = new MediaType(file.getPath(), MediaType.Type.UDISK);
/*  39 */         mediaTypes.add(mediaType);
/*  40 */       } else if (diskType.toUpperCase().contains("CD")) {
/*  41 */         MediaType mediaType = new MediaType(file.getPath(), MediaType.Type.CDROM);
/*  42 */         mediaTypes.add(mediaType);
/*     */       } 
/*     */     } 
/*     */     
/*  46 */     return mediaTypes;
/*     */   }
/*     */   
/*     */   private static List<MediaType> getLinuxLinkMedias() {
/*  50 */     File parent = new File("/dev");
/*  51 */     File[] drivers = parent.listFiles();
/*  52 */     List<MediaType> mediaTypes = new ArrayList<>();
/*  53 */     assert drivers != null;
/*     */     
/*  55 */     for (File file : drivers) {
/*  56 */       String path = file.getAbsolutePath();
/*  57 */       if (path.startsWith("/dev/sd")) {
/*  58 */         Pattern p = Pattern.compile(".*\\d+$");
/*  59 */         Matcher m = p.matcher(path);
/*  60 */         if (!m.matches()) {
/*  61 */           MediaType mediaType = new MediaType(path, MediaType.Type.UDISK);
/*  62 */           mediaTypes.add(mediaType);
/*     */         } 
/*     */       } 
/*     */     } 
/*     */ 
/*     */     
/*  68 */     Iterator<MediaType> iterator = mediaTypes.iterator();
/*  69 */     while (iterator.hasNext()) {
/*  70 */       String name = ((MediaType)iterator.next()).getPath().substring(5);
/*  71 */       File file = new File("/sys/block/" + name + "/removable");
/*  72 */       if (file.isFile() && file.exists()) {
/*     */         try {
/*  74 */           BufferedReader br = new BufferedReader(new FileReader(file));
/*  75 */           String content = br.readLine();
/*  76 */           if (content.equals("0")) {
/*  77 */             iterator.remove();
/*     */           }
/*  79 */         } catch (IOException e) {
/*  80 */           log.error("", e.getCause());
/*     */         } 
/*     */       }
/*     */     } 
/*     */     
/*  85 */     MediaType cdMedia = new MediaType("/dev/sr0", MediaType.Type.CDROM);
/*  86 */     mediaTypes.add(cdMedia);
/*     */     
/*  88 */     return mediaTypes;
/*     */   }
/*     */ 
/*     */   
/*     */   public static DiskMemory getDiskMemory(String driveName) {
/*  93 */     if (isISOFile(driveName)) {
/*  94 */       DiskMemory diskMemory = new DiskMemory();
/*  95 */       File isoFile = new File(driveName);
/*  96 */       if (isoFile.exists() && isoFile.isFile()) {
/*  97 */         long fileLength = isoFile.length();
/*  98 */         int bytePerSector = 2048;
/*  99 */         int sectorCount = (int)(fileLength / bytePerSector);
/* 100 */         diskMemory.setBytePerSector(bytePerSector);
/* 101 */         diskMemory.setSectorCount(sectorCount);
/*     */       } 
/* 103 */       return diskMemory;
/*     */     } 
/* 105 */     return getUDiskFile(driveName);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public static DiskMemory getUDiskFile(String driveName) {
/* 116 */     if (OSUtils.isWin()) {
/* 117 */       return DiskMemory.getDiskMemory(driveName);
/*     */     }
/* 119 */     if (isExists(driveName)) {
/* 120 */       return DiskMemory.getDiskMemory(driveName);
/*     */     }
/* 122 */     return getNullDisk();
/*     */   }
/*     */ 
/*     */ 
/*     */   
/*     */   private static boolean isExists(String driveName) {
/* 128 */     File linuxFile = new File(driveName);
/* 129 */     return linuxFile.exists();
/*     */   }
/*     */   
/*     */   public static boolean isISOFile(String name) {
/* 133 */     return name.contains("iso");
/*     */   }
/*     */   
/*     */   public static boolean isICDRom(String name) {
/* 137 */     return name.contains("sr");
/*     */   }
/*     */   
/*     */   public static DiskMemory getNullDisk() {
/* 141 */     return new DiskMemory();
/*     */   }
/*     */   
/*     */   public static void main(String[] args) {}
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/core/protocol/vm/DiskFactory.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */