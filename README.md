# Yoach's AI Coaching Platform

Welcome to Yoach’s AI Coaching Platform repository. This project leverages **Mediapipe Realtime 3D Pose Estimation** alongside advanced AI modules (such as FACT, FineParser, and VideoLLM-online) to deliver an end-to-end coaching solution that transforms raw video inputs into personalized, actionable feedback. Our system supports multiple sports and fitness activities, providing detailed motion analysis and user-friendly guidance.

---
## Quick Start 

python mp03.py




## Table of Contents

- [Yoach's AI Coaching Platform](#yoachs-ai-coaching-platform)
  - [Quick Start](#quick-start)
  - [Table of Contents](#table-of-contents)
  - [Overall Goals \& Thought Process](#overall-goals--thought-process)
    - [Goal](#goal)
    - [Thought Process](#thought-process)
  - [System Design](#system-design)
    - [Data Ingestion](#data-ingestion)
    - [2D Pose Detection](#2d-pose-detection)
    - [3D Pose Estimation](#3d-pose-estimation)
    - [Skeleton Feature Extraction](#skeleton-feature-extraction)
    - [Sub-Action Segmentation](#sub-action-segmentation)
    - [Action Error Detection \& Scoring](#action-error-detection--scoring)
    - [VideoLLM (Feedback Dialogue)](#videollm-feedback-dialogue)
    - [Visualization \& UI](#visualization--ui)
  - [Why This Architecture?](#why-this-architecture)
    - [Modularity \& Replaceability](#modularity--replaceability)
    - [Efficiency \& Scalability](#efficiency--scalability)
    - [Adaptability](#adaptability)
    - [User-Centered Design](#user-centered-design)
  - [Examples \& Scenarios](#examples--scenarios)
    - [Badminton Forehand Smash](#badminton-forehand-smash)
    - [Golf Swing Training](#golf-swing-training)
    - [Fitness/Workout Correction (e.g., Squats)](#fitnessworkout-correction-eg-squats)
  - [Ongoing Developments \& Latest Improvements](#ongoing-developments--latest-improvements)
  - [Future Directions](#future-directions)
  - [Key Takeaways](#key-takeaways)
  - [Final Note](#final-note)

---

## Overall Goals & Thought Process

### Goal
- **End-to-End Coaching:** Deliver a comprehensive AI coaching solution guiding users from raw video capture to detailed, coach-level feedback.
- **Multi-Sport Support:** Cater to various sports (e.g., badminton, tennis, golf, workouts) by providing sport-specific motion analysis.
- **Actionable Insights:** Convert complex biomechanical data into clear, actionable advice.

### Thought Process
1. **Capture:** Record user performance using everyday devices (e.g., smartphones, webcams).
2. **Analyze:**
   - **Mediapipe 3D Pose Estimation:** Converts 2D keypoints into a full 3D skeleton (x, y, z coordinates).
   - **Sub-Action Segmentation:** Uses models like **FACT** or **FineParser** to segment the motion into phases (e.g., “backswing,” “impact”).
   - **Error Detection & Scoring:** Compares user motion with expert benchmarks to quantify deviations.
3. **Explain:** Leverage **VideoLLM-online** to translate numerical and biomechanical data into natural language feedback.
4. **Visualize:** Overlay analysis and feedback on the original video, making it easy for users to see and understand corrective measures.

---

## System Design

Our architecture is modular, allowing each component to be independently updated or replaced as advancements occur.

### Data Ingestion
- **What Happens:** Users upload or stream a video of their performance.
- **Preprocessing:** The video is trimmed, frames are extracted, and resolution is standardized to ensure consistent input.

### 2D Pose Detection
- **Model:** Advanced 2D detectors (e.g., AlphaPose + Halpe 26) capture 26 key joints.
- **Output:** (x, y) coordinates and confidence scores for each detected joint.
- **Purpose:** Establishes the foundational data required for 3D pose estimation.

### 3D Pose Estimation
- **Model:** **Mediapipe Realtime 3D Pose Estimation**
- **Task:** Converts 2D keypoints into detailed 3D skeleton data (x, y, z coordinates).
- **Purpose:** Provides in-depth biomechanical insights (angles, velocities, and posture metrics).

### Skeleton Feature Extraction
- **Tasks:**
  - Normalize the skeleton by aligning key reference points.
  - Compute joint angles, velocities, and accelerations.
- **Purpose:** Transform raw 3D data into actionable metrics for performance analysis.

### Sub-Action Segmentation
- **Models:** 
  - **FACT (Frame-Action Cross-Attention)**
  - **FineParser**
- **Task:** Identify and segment the movement into distinct sub-actions (e.g., “backswing,” “forward swing,” “impact,” “follow-through”).
- **Purpose:** Pinpoint where deviations occur during different movement phases for targeted feedback.

### Action Error Detection & Scoring
- **Process:** 
  - Compare the extracted 3D features against an “ideal” expert motion model.
  - Quantify discrepancies in joint angles, timing, and speed.
- **Output:** Specific error messages (e.g., “Elbow angle is 10° off”) that indicate how the performance can be improved.
- **Purpose:** Bridge the gap between raw data and actionable coaching insights.

### VideoLLM (Feedback Dialogue)
- **Model:** **VideoLLM-online** (using GPT-4, Llama, or similar models)
- **Task:** Convert structured error data and segmentation results into human-friendly, conversational coaching advice.
- **Features:**
  - Real-time Q&A support.
  - Multi-lingual and adaptive feedback based on user skill level.
- **Purpose:** Ensure the technical analysis is transformed into clear, context-aware coaching recommendations.

### Visualization & UI
- **Implementation:** Python-based or web-based overlay.
- **Features:**
  - Render the original video with a dynamic skeleton overlay.
  - Display color-coded markers, numeric differences, and coaching text.
- **Purpose:** Provide a visual representation that helps users directly see the areas needing improvement.

---

## Why This Architecture?

### Modularity & Replaceability
- **Independent Modules:** Each component (pose estimation, segmentation, error detection, LLM) can be updated or swapped without re-engineering the entire system.
- **Future-Proof:** Easily integrate future technological advancements.

### Efficiency & Scalability
- **Pipeline Processing:** Breaking the analysis into distinct stages allows for parallel processing, which is ideal for real-time or near-real-time analysis.
- **Containerization:** Components can be containerized (e.g., using Docker) to scale dynamically with usage.

### Adaptability
- **Sport-Specific Customization:** Adjust expert reference data and segmentation parameters to support a variety of sports.
- **Dynamic Rule Engine:** Store scoring thresholds in flexible formats (like JSON) for quick tuning based on different user profiles.

### User-Centered Design
- **Actionable Feedback:** Combines quantitative analysis with natural language explanations to deliver clear, actionable coaching.
- **Visual Guidance:** Overlays and UI elements help users understand exactly where and how to improve their performance.

---

## Examples & Scenarios

### Badminton Forehand Smash
- **Process:** A 5-second video is segmented into “preparation,” “backswing,” “forward swing,” “impact,” and “follow-through.”
- **Feedback:** “During your backswing, your elbow is 8° lower than recommended; speed up your forward swing for a stronger smash.”
- **Visualization:** Color-coded overlays highlight the incorrect elbow positioning during the backswing.

### Golf Swing Training
- **Process:** A 10-second drive shot is analyzed.
- **Feedback:** “Your hip rotation is under-rotated by 10°. Rotate your pelvis further for more torque and power.”
- **Visualization:** Markers on the hips indicate the under-rotation.

### Fitness/Workout Correction (e.g., Squats)
- **Process:** The movement is segmented into “descent,” “bottom hold,” and “ascent.”
- **Feedback:** “Keep your back neutral and prevent your knees from moving too far forward to avoid strain.”
- **Visualization:** Real-time overlay displays joint angle measurements and corrective cues.

---

## Ongoing Developments & Latest Improvements

- **VideoLLM-online Integration:** Exploring real-time feedback mechanisms, especially for AR devices and smart glasses.
- **Enhanced Sub-Action Segmentation:** Using **FineParser** for finer-grained segmentation of complex movements.
- **Expanded Expert Reference Library:** Building a flexible database of ideal motion patterns across multiple sports.
- **UI Enhancements:** Improved color-coded overlays and interactive markers for better user engagement.
- **LLM Safety & Specificity:** Enhanced prompt engineering to ensure safe, accurate, and contextually grounded coaching advice.

---

## Future Directions

- **Multi-Person Support:** Extend capabilities to analyze and compare multiple players or interactions within the same scene.
- **Adaptive Feedback:** Develop models that adjust feedback strictness based on user proficiency (beginner vs. advanced).
- **Augmented Reality Integration:** Enable real-time suggestions via smart glasses or AR devices.
- **Broader Sports Coverage:** Expand to support additional sports and fitness activities, including winter sports and track & field events.

---

## Key Takeaways

- **Comprehensive Pipeline:**  
  **Video Capture → 2D Detection → Mediapipe-based 3D Pose Estimation → Feature Extraction → Sub-Action Segmentation → Error Detection & Scoring → VideoLLM-driven Coaching → Visual Feedback**
- **Critical Modules:**  
  - **FACT/FineParser:** Accurately segment the motion into actionable sub-actions.
  - **Error Detection & Scoring:** Precisely measure deviations from ideal performance.
  - **VideoLLM-online:** Translates technical data into clear, actionable coaching advice.
- **User Benefits:**  
  - **Data-Driven Insights:** Professional-level feedback to help users understand and improve their performance.
  - **Visual & Textual Guidance:** Clear overlays and natural language explanations make it easier to identify and correct mistakes.
  - **Flexible Analysis:** Supports both real-time feedback and detailed post-session analysis.

---

## Final Note

Yoach’s AI Coaching Platform is a modular, expandable solution that transforms raw video data into insightful, personalized coaching advice. By integrating **Mediapipe Realtime 3D Pose Estimation** with advanced sub-action segmentation (using FACT or FineParser), precise error detection, and natural language feedback via **VideoLLM-online**, our system empowers users to refine their technique—whether in sports, fitness, or beyond.

Stay tuned for more updates as we continue to refine our modules and expand the platform's capabilities. Feel free to explore, contribute, or reach out with any questions. Happy coaching!
