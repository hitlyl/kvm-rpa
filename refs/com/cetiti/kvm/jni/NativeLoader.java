/*     */ package com.cetiti.kvm.jni;
/*     */ import java.io.BufferedInputStream;
/*     */ import java.io.File;
/*     */ import java.io.FileOutputStream;
/*     */ import java.io.IOException;
/*     */ import java.io.InputStream;
/*     */ import java.net.JarURLConnection;
/*     */ import java.net.URISyntaxException;
/*     */ import java.net.URL;
/*     */ import java.util.Enumeration;
/*     */ import java.util.jar.JarEntry;
/*     */ import java.util.jar.JarFile;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import refs.com.cetiti.kvm.jni.NativeLoader;
import refs.com.hiklife.svc.util.OSUtils;
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
/*     */ public class NativeLoader
/*     */ {
/*  37 */   private static final Logger log = LoggerFactory.getLogger(NativeLoader.class);
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
/*     */   public static synchronized void loader(String dirPath) throws IOException, ClassNotFoundException, URISyntaxException {
/*  50 */     boolean isWin = OSUtils.isWin();
/*  51 */     boolean is64Bit = OSUtils.is64Bit();
/*  52 */     boolean isX86 = OSUtils.isX86();
/*     */     
/*  54 */     String pre = isWin ? "" : "lib";
/*     */     
/*  56 */     String isX86Pre = isX86 ? "_x86" : "_arm";
/*  57 */     String is64BitPre = is64Bit ? "_64" : "";
/*  58 */     String ext = isX86Pre + is64BitPre + (isWin ? ".dll" : ".so");
/*  59 */     Enumeration<URL> dir = Thread.currentThread().getContextClassLoader().getResources(pre + dirPath + ext);
/*  60 */     while (dir.hasMoreElements()) {
/*  61 */       URL url = dir.nextElement();
/*  62 */       String protocol = url.getProtocol();
/*  63 */       if ("jar".equals(protocol)) {
/*  64 */         File path = new File(".");
/*  65 */         String rootOutputPath = path.getAbsoluteFile().getParent() + File.separator;
/*  66 */         File tempFile = new File(rootOutputPath + File.separator + pre + dirPath + ext);
/*  67 */         if (tempFile.exists()) {
/*  68 */           loadFileNative(tempFile); continue;
/*     */         } 
/*  70 */         JarURLConnection jarURLConnection = (JarURLConnection)url.openConnection();
/*  71 */         JarFile jarFile = jarURLConnection.getJarFile();
/*  72 */         Enumeration<JarEntry> entries = jarFile.entries();
/*  73 */         while (entries.hasMoreElements()) {
/*  74 */           JarEntry jarEntry = entries.nextElement();
/*  75 */           String entityName = jarEntry.getName();
/*  76 */           if (jarEntry.isDirectory() || !entityName.startsWith(pre + dirPath)) {
/*     */             continue;
/*     */           }
/*  79 */           if (entityName.endsWith(ext))
/*  80 */             loadJarNative(jarEntry); 
/*     */         } 
/*     */         continue;
/*     */       } 
/*  84 */       if ("file".equals(protocol)) {
/*  85 */         File file = new File(url.toURI().getPath());
/*  86 */         loadFileNative(file);
/*     */       } 
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static void loadFileNative(File file) {
/* 100 */     if (null == file) {
/*     */       return;
/*     */     }
/* 103 */     if (file.isDirectory()) {
/* 104 */       File[] files = file.listFiles();
/* 105 */       if (null != files) {
/* 106 */         for (File f : files) {
/* 107 */           loadFileNative(f);
/*     */         }
/*     */       }
/*     */     } 
/* 111 */     if (file.canRead()) {
/*     */       try {
/* 113 */         System.load(file.getPath());
/* 114 */         log.debug("加载native文件,file :{}成功!", file.getPath());
/* 115 */       } catch (UnsatisfiedLinkError e) {
/* 116 */         log.error("加载native文件 :{}失败!请确认操作系统是X86还是X64!", file, e);
/*     */       } 
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private static void loadJarNative(JarEntry jarEntry) {
/* 130 */     File path = new File(".");
/* 131 */     String rootOutputPath = path.getAbsoluteFile().getParent() + File.separator;
/* 132 */     String entityName = jarEntry.getName();
/* 133 */     File tempFile = new File(rootOutputPath + File.separator + entityName);
/* 134 */     if (!tempFile.getParentFile().exists()) {
/* 135 */       tempFile.getParentFile().mkdirs();
/*     */     }
/* 137 */     if (tempFile.exists()) {
/* 138 */       loadFileNative(tempFile);
/*     */       return;
/*     */     } 
/* 141 */     InputStream in = null;
/* 142 */     BufferedInputStream reader = null;
/* 143 */     FileOutputStream writer = null;
/*     */     try {
/* 145 */       in = NativeLoader.class.getResourceAsStream(entityName);
/* 146 */       if (in == null) {
/* 147 */         in = NativeLoader.class.getResourceAsStream("/" + entityName);
/* 148 */         if (null == in) {
/*     */           return;
/*     */         }
/*     */       } 
/* 152 */       reader = new BufferedInputStream(in);
/* 153 */       writer = new FileOutputStream(tempFile);
/* 154 */       byte[] buffer = new byte[reader.available()];
/* 155 */       reader.read(buffer);
/* 156 */       writer.write(buffer);
/*     */     }
/* 158 */     catch (IOException e) {
/* 159 */       log.error(e.toString());
/*     */     } 
/*     */     try {
/* 162 */       if (in != null) {
/* 163 */         in.close();
/*     */       }
/* 165 */       if (writer != null) {
/* 166 */         writer.close();
/*     */       }
/* 168 */     } catch (IOException e) {
/* 169 */       log.error(e.toString());
/*     */     } 
/*     */     try {
/* 172 */       System.load(tempFile.getPath());
/* 173 */       log.debug("加载native文件,jar :{}成功!", tempFile);
/* 174 */     } catch (UnsatisfiedLinkError e) {
/* 175 */       log.error("加载native文件 :{}失败!请确认操作系统是X86还是X64!", tempFile);
/*     */     } 
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/cetiti/kvm/jni/NativeLoader.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */