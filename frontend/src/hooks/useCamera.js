/**
 * useCamera — Custom hook for managing device camera access.
 *
 * Handles getUserMedia lifecycle, frame capture at configurable FPS,
 * and cleanup on unmount.
 */

import { useRef, useState, useCallback, useEffect } from 'react';

const DEFAULT_FPS = 5;

export function useCamera(fps = DEFAULT_FPS) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Start the camera and begin capturing frames.
   * @returns {Promise<void>}
   */
  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Create offscreen canvas for frame capture
      if (!canvasRef.current) {
        canvasRef.current = document.createElement('canvas');
      }

      setIsActive(true);
    } catch (err) {
      console.error('Camera access failed:', err);
      setError(err.message || 'Camera access denied');
      setIsActive(false);
    }
  }, []);

  /**
   * Stop the camera and release resources.
   */
  const stopCamera = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
  }, []);

  /**
   * Capture a single frame as a base64 JPEG string.
   * @returns {string|null} Base64-encoded JPEG data (without data URI prefix).
   */
  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || !isActive || video.readyState < 2) {
      return null;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    // Get base64 JPEG — strip the data URI prefix
    const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
    return dataUrl.split(',')[1];
  }, [isActive]);

  /**
   * Start a frame capture loop at the configured FPS.
   * @param {function} onFrame - Callback receiving base64 frame data.
   * @returns {function} Cleanup function to stop the loop.
   */
  const startFrameLoop = useCallback(
    (onFrame) => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }

      const interval = 1000 / fps;
      intervalRef.current = setInterval(() => {
        const frame = captureFrame();
        if (frame) {
          onFrame(frame);
        }
      }, interval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    },
    [fps, captureFrame]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
    videoRef,
    isActive,
    error,
    startCamera,
    stopCamera,
    captureFrame,
    startFrameLoop,
  };
}
