# wavefront-obj-2
An unofficial update to the existing Wavefront OBJ 3D-model file format.

## Overview

Wavefront OBJ 2.0 adds animation support, and has future plans to include texture data inside the file.

## Key Features

- **Backward Compatible**: Standard OBJ parsers ignore animation keywords
- **Sparse Updates**: Only specify vertices that actually move
- **Multiple Animations**: Support for multiple named animation sequences per file
- **Keyframe-Based**: Define keyframes with automatic linear interpolation
- **Simple Syntax**: Minimal new keywords that follow OBJ conventions

## Format Specification

### New Keywords

#### `anim <name> <fps>`
Declares a new animation sequence.

- **name**: Animation name (quoted string)
- **fps**: Frame rate (frames per second, integer)

```
anim "Walk Cycle" 30
```

#### `frame <number>`
Declares a keyframe in the current animation.

- **number**: Frame number (integer, starts at 0)

```
frame 0
frame 10
frame 25
```

#### `vdelta <index> <dx> <dy> <dz>`
Specifies a vertex offset from the base mesh position (a.k.a. first frame's position.).

- **index**: Vertex index (1-based, matching OBJ convention)
- **dx dy dz**: Offset values added to the base vertex position

```
vdelta 1  2.0  0.0  0.0
vdelta 5  0.0  1.5  0.0
```

## Animation Behavior

### Cumulative Offsets
All `vdelta` values are **cumulative** - they represent the total offset from each vertex's original position in the base mesh, not from the previous frame.

**Example:**
```
v 0 0 0          # Base position

frame 0
vdelta 1  1.0  0.0  0.0    # Vertex at (1, 0, 0)

frame 10
vdelta 1  3.0  0.0  0.0    # Vertex at (3, 0, 0), NOT (4, 0, 0)
```

### Interpolation
Frames between defined keyframes are **linearly interpolated**.

**Example:**
```
frame 0
vdelta 1  0.0  0.0  0.0    # Position: (0, 0, 0)

frame 10
vdelta 1  10.0  0.0  0.0   # Position: (10, 0, 0)

# Frame 5 will automatically interpolate to (5, 0, 0)
# Frame 7 will automatically interpolate to (7, 0, 0)
```

### Unspecified Vertices
Vertices not mentioned in a `vdelta` statement remain at their current position (no movement).

## Complete Example

```
# Standard OBJ geometry
g Pyramid

v  0.0  0.0  0.0
v  1.0  0.0  0.0
v  1.0  1.0  0.0
v  0.0  1.0  0.0
v  0.5  0.5  1.6

f  1  2  3
f  1  3  4
f  1  4  5
f  2  5  3
f  3  5  4

# First animation: Translate entire pyramid
anim "Move Right" 30

frame 0
vdelta 1  2.0  2.0  2.0
vdelta 2  3.0  2.0  2.0
vdelta 3  3.0  3.0  2.0
vdelta 4  2.0  3.0  2.0
vdelta 5  2.5  2.5  3.6

frame 30
vdelta 1  5.0  2.0  2.0
vdelta 2  6.0  2.0  2.0
vdelta 3  6.0  3.0  2.0
vdelta 4  5.0  3.0  2.0
vdelta 5  5.5  2.5  3.6

# Second animation: Bounce
anim "Bounce" 60

frame 0
vdelta 5  0.0  0.0  0.0

frame 15
vdelta 5  0.0  0.0  2.0

frame 30
vdelta 5  0.0  0.0  0.0
```

## File Structure

A complete animated OBJ file follows this structure:

```
# 1. Standard OBJ header comments (optional)
# 2. Material library references (optional)
# 3. Object/group definitions
# 4. Vertex definitions (v)
# 5. Texture coordinates (vt) - optional
# 6. Normals (vn) - optional
# 7. Face definitions (f)
# 8. Animation sequences (anim, frame, vdelta)
```

**Important**: All standard OBJ geometry must be defined before animation sequences begin.

## Multiple Animations

Multiple animations can be defined sequentially. Each `anim` keyword starts a new animation and implicitly ends the previous one.

```
anim "Walk" 30
frame 0
vdelta 1  0.0  0.0  0.0
frame 10
vdelta 1  1.0  0.0  0.0

anim "Run" 60
frame 0
vdelta 1  0.0  0.0  0.0
frame 5
vdelta 1  2.0  0.0  0.0
```

## Best Practices

### Keyframe Placement
- Only define keyframes where significant changes occur
- Let linear interpolation handle smooth transitions
- More keyframes = more precise control but larger files

### Performance
- Specify only vertices that actually move in each frame
- Group related vertex movements in the same frame
- Consider vertex count when designing complex animations

### Organization
- Use descriptive animation names
- Keep frame rates consistent within similar animations
- Comment your keyframes for complex sequences

## Compatibility

### Backward Compatibility
Standard OBJ parsers will:
- Successfully load the geometry
- Ignore all animation keywords
- Display the base mesh in its original position

### Forward Compatibility
Parsers supporting this extension should:
- Validate frame numbers are sequential within animations
- Handle missing intermediate frames through interpolation
- Support 1-based vertex indexing consistently
- Reject invalid syntax gracefully

## Technical Notes

### Indexing
- Vertex indices are **1-based** (matching OBJ standard)
- Frame numbers are **0-based** (matching common animation conventions)

### Precision
- Coordinate values support floating-point precision
- Frame rates are integers only

### Limitations
- Only vertex positions can be animated (no UV, normals, or topology changes)
- Linear interpolation only (no bezier curves or custom easing)
- All animations share the same base mesh geometry

## File Extension

Animated OBJ files can use either:
- `.obj` - For backward compatibility
- `.aobj` - To explicitly indicate animation support

## License

This format extension is released into the public domain. Implementers are free to use, modify, and distribute parsers and exporters without restriction.

## Version

**Specification Version**: 1.0  
**Last Updated**: 2026

---

*For questions, suggestions, or to report issues with this specification, please contact the format maintainer.*
