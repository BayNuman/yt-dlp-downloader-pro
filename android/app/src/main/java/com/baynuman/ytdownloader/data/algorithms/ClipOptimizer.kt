package com.baynuman.ytdownloader.data.algorithms

data class MicroClip(
    val start: Float,
    val end: Float,
    val title: String
)

data class MacroClip(
    val start: Float,
    val end: Float,
    val subClips: List<MicroClip>
)

object ClipOptimizer {
    /**
     * Greedy Interval Merging (LeetCode 56) algorithm implementation in Kotlin.
     * Merges micro-clips whose start times are close within thresholdSec to minimize download network requests.
     */
    fun optimizeClipIntervals(clips: List<MicroClip>, thresholdSec: Float = 30f): List<MacroClip> {
        if (clips.isEmpty()) return emptyList()
        val sorted = clips.sortedBy { it.start }
        val merged = mutableListOf<MacroClip>()

        var currentStart = sorted[0].start
        var currentEnd = sorted[0].end
        val currentSubClips = mutableListOf(sorted[0])

        for (i in 1 until sorted.size) {
            val next = sorted[i]
            if (next.start <= currentEnd + thresholdSec) {
                // Merge overlapping or close interval ranges
                currentEnd = maxOf(currentEnd, next.end)
                currentSubClips.add(next)
            } else {
                // Emit current MacroClip and initialize a new range
                merged.add(MacroClip(currentStart, currentEnd, currentSubClips.toList()))
                currentSubClips.clear()
                currentStart = next.start
                currentEnd = next.end
                currentSubClips.add(next)
            }
        }
        merged.add(MacroClip(currentStart, currentEnd, currentSubClips.toList()))
        return merged
    }
}
