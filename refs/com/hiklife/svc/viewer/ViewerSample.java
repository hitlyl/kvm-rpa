/*     */ package com.hiklife.svc.viewer;
/*     */ import java.awt.Color;
/*     */ import java.awt.Graphics;
/*     */ import java.awt.Graphics2D;
/*     */ import java.awt.Image;
/*     */ import java.awt.Point;
/*     */ import java.awt.Toolkit;
/*     */ import java.awt.event.FocusAdapter;
/*     */ import java.awt.event.FocusEvent;
/*     */ import java.awt.event.MouseAdapter;
/*     */ import java.awt.event.MouseEvent;
/*     */ import java.awt.image.BufferedImage;
/*     */ import java.awt.image.MemoryImageSource;
/*     */ import javax.swing.JComponent;
/*     */ import org.bytedeco.ffmpeg.avutil.AVFrame;
/*     */ import org.slf4j.Logger;
/*     */ import org.slf4j.LoggerFactory;

import com.hiklife.svc.core.protocol.ProtocolContext;
import com.hiklife.svc.core.protocol.baseinfo.VersionPacket;
import com.hiklife.svc.core.protocol.handler.ProtocolDeviceInfoEvent;
import com.hiklife.svc.core.protocol.handler.ProtocolHandlerImpl;
import com.hiklife.svc.core.protocol.handler.ProtocolViewerEvent;
import com.hiklife.svc.core.protocol.normal.WriteNormalType;

import refs.com.hiklife.svc.Kvm4JSdk;
import refs.com.hiklife.svc.core.protocol.ProtocolHandler;
import refs.com.hiklife.svc.core.protocol.baseinfo.DevicePacket;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolAuthEvent;
import refs.com.hiklife.svc.core.protocol.handler.ProtocolConnectEvent;
import refs.com.hiklife.svc.core.protocol.normal.AudioParamPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastSetResultPacket;
import refs.com.hiklife.svc.core.protocol.normal.BroadcastStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyEventPacket;
import refs.com.hiklife.svc.core.protocol.normal.KeyStatusPacket;
import refs.com.hiklife.svc.core.protocol.normal.MouseTypePacket;
import refs.com.hiklife.svc.core.protocol.normal.VideoParamPacket;
import refs.com.hiklife.svc.core.protocol.security.SecurityType;
import refs.com.hiklife.svc.jnative.NativeLibFactory;
import refs.com.hiklife.svc.util.HexUtils;
import refs.com.hiklife.svc.util.UIKit;
import refs.com.hiklife.svc.viewer.AudioPlayTrack;
import refs.com.hiklife.svc.viewer.KeyEventListener;
import refs.com.hiklife.svc.viewer.MouseEventListener;
import refs.com.hiklife.svc.viewer.Option;
import refs.com.hiklife.svc.viewer.RelativeMouseEventListener;
import refs.com.hiklife.svc.viewer.Viewer;
import refs.com.hiklife.svc.viewer.ViewerEvent;
import refs.com.hiklife.svc.viewer.ViewerSample;
import refs.com.hiklife.svc.viewer.WorkThreadPool;
/*     */ 
/*     */ public class ViewerSample extends JComponent implements ProtocolConnectEvent, ProtocolAuthEvent, ProtocolViewerEvent, ProtocolDeviceInfoEvent, Viewer {
/*  36 */   private static final Logger log = LoggerFactory.getLogger(ViewerSample.class);
/*  37 */   double scaleX = 1.0D;
/*  38 */   double scaleY = 1.0D;
/*     */   int imageWidth;
/*     */   int imageHeight;
/*     */   private final ProtocolHandler protocolHandler;
/*     */   private final ViewerEvent viewerEvent;
/*     */   private BufferedImage bufferedImage;
/*     */   private KeyEventListener keyEventListener;
/*     */   private MouseEventListener mouseEventListener;
/*     */   private RelativeMouseEventListener nativeMouseEventListener;
/*     */   private AudioPlayTrack audioPlayTrack;
/*     */   int offsetX;
/*     */   int offsetY;
/*  50 */   private final int moveStep = 5;
/*     */   
/*     */   private boolean isClipped;
/*     */   private int width;
/*     */   private int height;
/*  55 */   private final Point lastPoint = new Point(0, 0);
/*  56 */   private int mouseType = 0;
/*  57 */   private int lastMouseType = 0;
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ViewerSample(String ip, int port, int channelNo, ViewerEvent event) {
/*  67 */     this.viewerEvent = event;
/*  68 */     setBackground(new Color(0, 0, 0));
/*  69 */     setFocusTraversalKeysEnabled(false);
/*  70 */     this.protocolHandler = (ProtocolHandler)new ProtocolHandlerImpl();
/*  71 */     this.protocolHandler.addConnectEvent(this);
/*  72 */     this.protocolHandler.addViewerEvent(this);
/*  73 */     this.protocolHandler.addAuthEvent(this);
/*  74 */     this.protocolHandler.addDeviceInfoEvent(this);
/*  75 */     WorkThreadPool.getInstance().execute(() -> Kvm4JSdk.connectViewer(ip, port, channelNo, this.protocolHandler));
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */     
/*  81 */     initAction();
/*  82 */     enableInputMethods(false);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   private void initAction() {
/*  89 */     addMouseMotionListener(new MouseAdapter()
/*     */         {
/*     */           public void mouseMoved(MouseEvent e) {
/*  92 */             if (e.getX() > ViewerSample.this.width - 5 && ViewerSample.this.offsetX >= e.getX() - ViewerSample.this.imageWidth + 5) {
/*  93 */               ViewerSample.this.offsetX -= 5;
/*  94 */             } else if (e.getX() < 5 && ViewerSample.this.offsetX <= -5) {
/*  95 */               ViewerSample.this.offsetX += 5;
/*     */             } 
/*  97 */             if (e.getY() > ViewerSample.this.height - 5 && ViewerSample.this.offsetY >= e.getY() - ViewerSample.this.imageHeight + 5) {
/*  98 */               ViewerSample.this.offsetY -= 5;
/*  99 */             } else if (e.getY() < 5 && ViewerSample.this.offsetY <= -5) {
/* 100 */               ViewerSample.this.offsetY += 5;
/*     */             } 
/*     */           }
/*     */         });
/* 104 */     addMouseListener(new MouseAdapter()
/*     */         {
/*     */           public void mouseClicked(MouseEvent evt) {
/* 107 */             ViewerSample.this.requestFocus();
/* 108 */             ViewerSample.this.clipCursor(evt);
/*     */           }
/*     */         });
/* 111 */     addFocusListener(new FocusAdapter()
/*     */         {
/*     */           public void focusGained(FocusEvent e) {
/* 114 */             ViewerSample.log.debug("focusGained");
/* 115 */             ViewerSample.this.viewerEvent.onFocusGained();
/*     */           }
/*     */ 
/*     */           
/*     */           public void focusLost(FocusEvent e) {
/* 120 */             ViewerSample.log.debug("focusLost");
/*     */             
/* 122 */             ViewerSample.this.quitSingleMouse();
/* 123 */             if (ViewerSample.this.keyEventListener != null) {
/* 124 */               ViewerSample.this.keyEventListener.focusLost(e);
/*     */             }
/*     */           }
/*     */         });
/*     */   }
/*     */   
/*     */   private void clipCursor(MouseEvent evt) {
/* 131 */     if (Option.instance.getEnableHideLocalMouse() == 1 && !this.isClipped) {
/* 132 */       requestFocus();
/* 133 */       int left = evt.getXOnScreen() - evt.getX();
/* 134 */       int right = left + getWidth();
/* 135 */       int top = evt.getYOnScreen() - evt.getY();
/* 136 */       int bottom = top + getHeight();
/*     */       
/* 138 */       if (this.nativeMouseEventListener == null) {
/* 139 */         this.nativeMouseEventListener = new RelativeMouseEventListener(this, this.lastPoint.x, this.lastPoint.y);
/*     */       }
/* 141 */       int result = NativeLibFactory.createJnaLib().clipCursor(left, top, right, bottom, this.nativeMouseEventListener);
/* 142 */       if (result == 0) {
/* 143 */         this.lastMouseType = this.mouseType;
/* 144 */         if (this.mouseType == 1) {
/* 145 */           writeMouseTypeREL();
/*     */         }
/* 147 */         this.isClipped = true;
/* 148 */         hideCursor();
/* 149 */         removeMouseListener(this.mouseEventListener);
/* 150 */         removeMouseMotionListener(this.mouseEventListener);
/* 151 */         removeMouseWheelListener(this.mouseEventListener);
/* 152 */       } else if (result == -1) {
/* 153 */         this.viewerEvent.onSingleMouseAccessDenied();
/*     */       } else {
/* 155 */         log.error("clipCursor error");
/*     */       } 
/*     */     } 
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void quitSingleMouse() {
/* 164 */     if (this.isClipped) {
/* 165 */       NativeLibFactory.createJnaLib().releaseCursor();
/* 166 */       setCursor(new Cursor(0));
/* 167 */       this.isClipped = false;
/* 168 */       addMouseListener(this.mouseEventListener);
/* 169 */       addMouseMotionListener(this.mouseEventListener);
/* 170 */       addMouseWheelListener(this.mouseEventListener);
/* 171 */       if (this.lastMouseType == 1) {
/* 172 */         writeMouseTypeABS();
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
/*     */   public BufferedImage getCurrentFrame() {
/* 184 */     return this.bufferedImage;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   protected void destroy() {
/* 191 */     NativeLibFactory.createJnaLib().releaseCursor();
/* 192 */     if (this.audioPlayTrack != null) {
/* 193 */       this.audioPlayTrack.destroy();
/*     */     }
/*     */     
/* 196 */     this.viewerEvent.onBeforeDestroy();
/*     */ 
/*     */ 
/*     */ 
/*     */     
/* 201 */     this.protocolHandler.graceClose();
/* 202 */     this.viewerEvent.onAfterDestroy();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   protected void hideCursor() {
/* 209 */     Image image = Toolkit.getDefaultToolkit().createImage(new MemoryImageSource(0, 0, new int[0], 0, 0));
/*     */     
/* 211 */     setCursor(Toolkit.getDefaultToolkit().createCustomCursor(image, new Point(0, 0), null));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   protected void paintComponent(Graphics g) {
/* 222 */     Graphics2D g2d = (Graphics2D)g;
/* 223 */     if (this.bufferedImage == null) {
/* 224 */       g2d.setPaint(Color.BLACK);
/* 225 */       g2d.fillRect(0, 0, getWidth(), getHeight());
/*     */     } else {
/* 227 */       this.width = getWidth();
/* 228 */       this.height = getHeight();
/* 229 */       this.imageHeight = this.bufferedImage.getHeight();
/* 230 */       this.imageWidth = this.bufferedImage.getWidth();
/* 231 */       if (Option.instance.getEnableImageScale() == 0 && Option.instance.getEnableFullScreen() == 1) {
/* 232 */         g2d.drawImage(this.bufferedImage, this.offsetX, this.offsetY, this.imageWidth, this.imageHeight, null);
/* 233 */         this.scaleX = 1.0D;
/* 234 */         this.scaleY = 1.0D;
/*     */       } else {
/* 236 */         g2d.drawImage(this.bufferedImage, 0, 0, this.width, this.height, null);
/* 237 */         this.scaleX = this.width / this.imageWidth;
/* 238 */         this.scaleY = this.height / this.imageHeight;
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
/*     */   public void onUpdateFrame(AVFrame avFrame) {
/* 250 */     if (avFrame == null) {
/*     */       return;
/*     */     }
/* 253 */     if (this.bufferedImage == null) {
/* 254 */       this.bufferedImage = UIKit.getBufferedImage(avFrame, null);
/*     */       
/* 256 */       this.viewerEvent.onDrawFirstFrame(this.bufferedImage);
/*     */     } else {
/* 258 */       this.bufferedImage = UIKit.getBufferedImage(avFrame, this.bufferedImage);
/*     */     } 
/* 260 */     repaint();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onUpdateAudio(byte[] bytes) {
/* 270 */     if (this.audioPlayTrack != null) {
/* 271 */       this.audioPlayTrack.play(bytes);
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
/*     */   public void onConnectSuccess(IoSession session) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onConnectFailed() {
/* 291 */     quitSingleMouse();
/* 292 */     this.viewerEvent.onConnectFailed("连接超时");
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onConnectClose(String closeInfo) {
/* 302 */     quitSingleMouse();
/* 303 */     if (this.protocolHandler.isBeforeNormal()) {
/* 304 */       this.viewerEvent.onConnectFailed("会话启动失败");
/*     */     }
/* 306 */     else if (closeInfo != null) {
/* 307 */       this.viewerEvent.onConnectFailed(closeInfo);
/*     */     } else {
/* 309 */       this.viewerEvent.onConnectFailed("已断开连接");
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
/*     */   public void onRequireAuth(SecurityType.Type type) {
/* 321 */     this.viewerEvent.onRequireAuth(type);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onGetDevice(DevicePacket device) {
/* 331 */     this
/*     */ 
/*     */       
/* 334 */       .audioPlayTrack = new AudioPlayTrack((device.getDeviceTypeInt() == 18 || device.getDeviceTypeInt() == 61 || device.getDeviceTypeInt() == 66));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onGetVersion(VersionPacket version) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onInvalidRFBMessageException(Throwable cause) {
/* 354 */     this.viewerEvent.onCaughtException(cause);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onCaughtException(Throwable cause) {
/* 364 */     this.viewerEvent.onCaughtException(cause);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onAuthSuccess() {
/* 372 */     this.viewerEvent.onAuthSuccess();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onAuthFailed(String msg) {
/* 382 */     this.viewerEvent.onAuthFailed(msg);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onReadImageInfo(int width, int height) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onAfterInitialisation() {
/* 401 */     requestFocus();
/* 402 */     this.keyEventListener = new KeyEventListener(this);
/* 403 */     this.mouseEventListener = new MouseEventListener(this);
/* 404 */     addMouseListener(this.mouseEventListener);
/* 405 */     addMouseMotionListener(this.mouseEventListener);
/* 406 */     addMouseWheelListener(this.mouseEventListener);
/*     */     
/* 408 */     addKeyListener(this.keyEventListener);
/*     */     
/* 410 */     this.viewerEvent.onAfterInitialisation();
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
/*     */   public void onChangeImageInfo(int width, int height) {}
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onVideoParam(VideoParamPacket videoParamPacket) {
/* 431 */     this.viewerEvent.onReadVideoParam(videoParamPacket);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onAudioParam(AudioParamPacket audioParamPacket) {
/* 441 */     this.viewerEvent.onReadAudioParam(audioParamPacket);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onReadMouseType(MouseTypePacket mouseTypePacket) {
/* 451 */     this.viewerEvent.onReadMouseType(mouseTypePacket);
/* 452 */     this.mouseType = mouseTypePacket.getType();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onBroadcastRequest(BroadcastStatusPacket broadcastStatusPacket) {
/* 462 */     this.viewerEvent.onReadBroadcastStatus(broadcastStatusPacket);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onBroadcastSet(BroadcastSetResultPacket broadcastSetResultPacket) {
/* 472 */     this.viewerEvent.onReadBroadcastSetResult(broadcastSetResultPacket);
/*     */   }
/*     */ 
/*     */   
/*     */   public void onWriteCustomMouseType(MouseTypePacket mouseTypePacket) {
/* 477 */     this.mouseType = mouseTypePacket.getType();
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
/*     */   public void callBackAuthInfo(SecurityType.Type type, String account, String password) {
/* 489 */     WorkThreadPool.getInstance().execute(() -> this.protocolHandler.callBackAuthInfo(type, account, password));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void stopSession() {
/* 499 */     destroy();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeBroadCastStatusRequest() {
/* 507 */     WorkThreadPool.getInstance().execute(this.protocolHandler::writeBroadCastStatusRequest);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeBroadCastSetRequest(byte[] channelSet, boolean keyBroadCast, boolean mouseBroadCast) {
/* 518 */     byte[] broadcastCloseMsg = new byte[68];
/* 519 */     broadcastCloseMsg[0] = -54;
/* 520 */     broadcastCloseMsg[2] = keyBroadCast ? 1 : 0;
/* 521 */     broadcastCloseMsg[3] = mouseBroadCast ? 1 : 0;
/* 522 */     System.arraycopy(channelSet, 0, broadcastCloseMsg, 4, 64);
/* 523 */     WorkThreadPool.getInstance().execute(() -> this.protocolHandler.writeBroadCastSetRequest(broadcastCloseMsg));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public ProtocolContext getContext() {
/* 533 */     return this.protocolHandler.getContext();
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public JComponent getJComponent() {
/* 543 */     return this;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeVideoParamRequest() {
/* 551 */     WorkThreadPool.getInstance().execute(this.protocolHandler::writeVideoParamRequest);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeVideoParam(VideoParamPacket videoParamPacket) {
/* 561 */     this.protocolHandler.writeCustomVideoParam(videoParamPacket);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeAudioParamRequest() {
/* 569 */     WorkThreadPool.getInstance().execute(this.protocolHandler::writeAudioParamRequest);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeAudioParam(boolean mute) {
/* 579 */     WorkThreadPool.getInstance().execute(() -> this.protocolHandler.writeCustomAudioParam(new AudioParamPacket(mute)));
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeMouseTypeRequest() {
/* 587 */     WorkThreadPool.getInstance().execute(this.protocolHandler::writeMouseTypeRequest);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeMouseType(int type) {
/* 597 */     WorkThreadPool.getInstance().execute(() -> this.protocolHandler.writeCustomMouseType(new MouseTypePacket(type)));
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeMouseTypeABS() {
/* 602 */     writeMouseType(1);
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeMouseTypeREL() {
/* 607 */     writeMouseType(0);
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeKeyStatusRequest() {
/* 615 */     WorkThreadPool.getInstance().execute(this.protocolHandler::writeKeyStateParamRequest);
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeMouseEvent(Point pos, int mask) {
/* 620 */     if (this.viewerEvent.onWriteMouseEvent(pos, mask)) {
/* 621 */       writeMouseEventByPass(pos, mask);
/*     */     }
/*     */   }
/*     */   
/*     */   public void writeMouse00() {
/* 626 */     writeMouseEventByPass(new Point(0, 0), 0);
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeMouseEventByPass(Point pos, int mask) {
/* 631 */     byte[] mouseBytes = encodeMouseEvent(pos.x, pos.y, mask);
/* 632 */     this.protocolHandler.writeMouseEvent(mouseBytes);
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
/*     */   private synchronized byte[] encodeMouseEvent(int x, int y, int mask) {
/* 644 */     if (x < 0) x = 0; 
/* 645 */     if (y < 0) y = 0;
/*     */ 
/*     */ 
/*     */     
/* 649 */     byte[] mouseMsg = new byte[6];
/* 650 */     mouseMsg[0] = WriteNormalType.PointerEvent.getCode();
/* 651 */     mouseMsg[1] = (byte)mask;
/* 652 */     byte[] xbyte = HexUtils.unsignedShortToRegister(x);
/* 653 */     System.arraycopy(xbyte, 0, mouseMsg, 2, 2);
/* 654 */     byte[] ybyte = HexUtils.unsignedShortToRegister(y);
/* 655 */     System.arraycopy(ybyte, 0, mouseMsg, 4, 2);
/* 656 */     return mouseMsg;
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeKeyEvent(KeyEventPacket keyEventPacket) {
/* 661 */     if (this.viewerEvent.onWriteKeyEvent(keyEventPacket.getDown(), keyEventPacket.getKey())) {
/* 662 */       writeKeyEventByPass(keyEventPacket);
/*     */     }
/*     */   }
/*     */   
/*     */   public void writeKeyEventByPass(KeyEventPacket keyEventPacket) {
/* 667 */     this.protocolHandler.writeKeyEvent(keyEventPacket);
/* 668 */     int key = keyEventPacket.getKey();
/* 669 */     if ((key == 65300 || key == 65509 || key == 65407) && keyEventPacket
/* 670 */       .getDown() == 0) {
/* 671 */       WorkThreadPool.getInstance().execute(this.protocolHandler::writeKeyStateParamRequest, 200L);
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeKeyEvent(KeyEventPacket[] keyEventPackets) {
/* 682 */     for (KeyEventPacket keyEventPacket : keyEventPackets) {
/* 683 */       writeKeyEvent(keyEventPacket);
/*     */     }
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void writeKeyEventByPass(KeyEventPacket[] keyEventPackets) {
/* 693 */     for (KeyEventPacket keyEventPacket : keyEventPackets) {
/* 694 */       writeKeyEventByPass(keyEventPacket);
/*     */     }
/*     */   }
/*     */ 
/*     */   
/*     */   public void writeKeyEvent(int key, int down) {
/* 700 */     KeyEventPacket keyEventPacket = new KeyEventPacket(down, key);
/* 701 */     writeKeyEvent(keyEventPacket);
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
/*     */ 
/*     */ 
/*     */   
/*     */   public ProtocolHandler getHandler() {
/* 716 */     return this.protocolHandler;
/*     */   }
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */ 
/*     */   
/*     */   public void onKeyStatus(KeyStatusPacket keyStatusPacket) {
/* 726 */     log.debug("Remote KeyStatusPacket:{}", keyStatusPacket);
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
/*     */ 
/*     */ 
/*     */ 
/*     */     
/* 753 */     this.viewerEvent.onReadKeyStatus(keyStatusPacket);
/*     */   }
/*     */   
/*     */   public Point getLastPoint() {
/* 757 */     return this.lastPoint;
/*     */   }
/*     */   
/*     */   public int getMouseType() {
/* 761 */     return this.mouseType;
/*     */   }
/*     */ }


/* Location:              /Users/liu/Documents/工作文档/珑琪/智能盒子/kvm/svc-console-master/lib/svc-sdk-1.3.4.1/!/com/hiklife/svc/viewer/ViewerSample.class
 * Java compiler version: 8 (52.0)
 * JD-Core Version:       1.1.3
 */