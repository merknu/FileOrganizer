"""
OpenCL Kernels for GPU-Accelerated Hashing
Provides high-performance SHA256 and MD5 implementations using OpenCL.
"""

# SHA256 OpenCL Kernel
SHA256_KERNEL = """
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable

// SHA256 constants
__constant uint k[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
};

// SHA256 initial hash values
__constant uint h0[8] = {
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

// Right rotate
#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

// SHA256 functions
#define CH(x, y, z) (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define EP0(x) (ROTR(x, 2) ^ ROTR(x, 13) ^ ROTR(x, 22))
#define EP1(x) (ROTR(x, 6) ^ ROTR(x, 11) ^ ROTR(x, 25))
#define SIG0(x) (ROTR(x, 7) ^ ROTR(x, 18) ^ ((x) >> 3))
#define SIG1(x) (ROTR(x, 17) ^ ROTR(x, 19) ^ ((x) >> 10))

__kernel void sha256_hash(__global const uchar* input, 
                         __global uint* output,
                         const uint input_length,
                         const uint num_chunks) {
    int gid = get_global_id(0);
    
    if (gid >= num_chunks) return;
    
    // Calculate chunk offset (each chunk is 64 bytes / 512 bits)
    int chunk_offset = gid * 64;
    
    // Initialize hash values for this chunk
    uint h[8];
    for (int i = 0; i < 8; i++) {
        h[i] = h0[i];
    }
    
    // Process the chunk
    uint w[64];
    
    // Copy chunk into first 16 words of w[]
    for (int i = 0; i < 16; i++) {
        w[i] = 0;
        if (chunk_offset + i * 4 + 3 < input_length) {
            w[i] = ((uint)input[chunk_offset + i * 4] << 24) |
                   ((uint)input[chunk_offset + i * 4 + 1] << 16) |
                   ((uint)input[chunk_offset + i * 4 + 2] << 8) |
                   ((uint)input[chunk_offset + i * 4 + 3]);
        } else {
            // Handle padding for last chunk
            for (int j = 0; j < 4; j++) {
                int byte_index = chunk_offset + i * 4 + j;
                if (byte_index < input_length) {
                    w[i] |= ((uint)input[byte_index] << (24 - j * 8));
                } else if (byte_index == input_length) {
                    // Add padding bit
                    w[i] |= (0x80 << (24 - j * 8));
                }
            }
        }
    }
    
    // Extend the first 16 words into the remaining 48 words w[16..63]
    for (int i = 16; i < 64; i++) {
        w[i] = SIG1(w[i - 2]) + w[i - 7] + SIG0(w[i - 15]) + w[i - 16];
    }
    
    // Initialize working variables
    uint a = h[0];
    uint b = h[1];
    uint c = h[2];
    uint d = h[3];
    uint e = h[4];
    uint f = h[5];
    uint g = h[6];
    uint h_val = h[7];
    
    // Compression function main loop
    for (int i = 0; i < 64; i++) {
        uint t1 = h_val + EP1(e) + CH(e, f, g) + k[i] + w[i];
        uint t2 = EP0(a) + MAJ(a, b, c);
        h_val = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }
    
    // Add the compressed chunk to the current hash value
    h[0] += a;
    h[1] += b;
    h[2] += c;
    h[3] += d;
    h[4] += e;
    h[5] += f;
    h[6] += g;
    h[7] += h_val;
    
    // Store result
    for (int i = 0; i < 8; i++) {
        output[gid * 8 + i] = h[i];
    }
}
"""

# MD5 OpenCL Kernel
MD5_KERNEL = """
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable

// MD5 functions
#define F(x, y, z) (((x) & (y)) | ((~x) & (z)))
#define G(x, y, z) (((x) & (z)) | ((y) & (~z)))
#define H(x, y, z) ((x) ^ (y) ^ (z))
#define I(x, y, z) ((y) ^ ((x) | (~z)))

// Left rotate
#define ROTLEFT(a, b) (((a) << (b)) | ((a) >> (32 - (b))))

// MD5 transform operations
#define FF(a, b, c, d, x, s, ac) { \\
    (a) += F((b), (c), (d)) + (x) + (uint)(ac); \\
    (a) = ROTLEFT((a), (s)); \\
    (a) += (b); \\
}

#define GG(a, b, c, d, x, s, ac) { \\
    (a) += G((b), (c), (d)) + (x) + (uint)(ac); \\
    (a) = ROTLEFT((a), (s)); \\
    (a) += (b); \\
}

#define HH(a, b, c, d, x, s, ac) { \\
    (a) += H((b), (c), (d)) + (x) + (uint)(ac); \\
    (a) = ROTLEFT((a), (s)); \\
    (a) += (b); \\
}

#define II(a, b, c, d, x, s, ac) { \\
    (a) += I((b), (c), (d)) + (x) + (uint)(ac); \\
    (a) = ROTLEFT((a), (s)); \\
    (a) += (b); \\
}

// MD5 initial values
__constant uint md5_init[4] = {
    0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476
};

__kernel void md5_hash(__global const uchar* input,
                      __global uint* output,
                      const uint input_length,
                      const uint num_chunks) {
    int gid = get_global_id(0);
    
    if (gid >= num_chunks) return;
    
    // Calculate chunk offset (each chunk is 64 bytes)
    int chunk_offset = gid * 64;
    
    // Initialize MD5 state
    uint a = md5_init[0];
    uint b = md5_init[1];
    uint c = md5_init[2];
    uint d = md5_init[3];
    
    // Process the chunk
    uint x[16];
    
    // Copy chunk data into x[] array (little-endian format)
    for (int i = 0; i < 16; i++) {
        x[i] = 0;
        if (chunk_offset + i * 4 + 3 < input_length) {
            x[i] = ((uint)input[chunk_offset + i * 4 + 3] << 24) |
                   ((uint)input[chunk_offset + i * 4 + 2] << 16) |
                   ((uint)input[chunk_offset + i * 4 + 1] << 8) |
                   ((uint)input[chunk_offset + i * 4]);
        } else {
            // Handle padding for last chunk
            for (int j = 0; j < 4; j++) {
                int byte_index = chunk_offset + i * 4 + j;
                if (byte_index < input_length) {
                    x[i] |= ((uint)input[byte_index] << (j * 8));
                } else if (byte_index == input_length) {
                    // Add padding bit
                    x[i] |= (0x80 << (j * 8));
                }
            }
        }
    }
    
    // MD5 transformation
    
    // Round 1
    FF(a, b, c, d, x[0],  7,  0xd76aa478);
    FF(d, a, b, c, x[1],  12, 0xe8c7b756);
    FF(c, d, a, b, x[2],  17, 0x242070db);
    FF(b, c, d, a, x[3],  22, 0xc1bdceee);
    FF(a, b, c, d, x[4],  7,  0xf57c0faf);
    FF(d, a, b, c, x[5],  12, 0x4787c62a);
    FF(c, d, a, b, x[6],  17, 0xa8304613);
    FF(b, c, d, a, x[7],  22, 0xfd469501);
    FF(a, b, c, d, x[8],  7,  0x698098d8);
    FF(d, a, b, c, x[9],  12, 0x8b44f7af);
    FF(c, d, a, b, x[10], 17, 0xffff5bb1);
    FF(b, c, d, a, x[11], 22, 0x895cd7be);
    FF(a, b, c, d, x[12], 7,  0x6b901122);
    FF(d, a, b, c, x[13], 12, 0xfd987193);
    FF(c, d, a, b, x[14], 17, 0xa679438e);
    FF(b, c, d, a, x[15], 22, 0x49b40821);
    
    // Round 2
    GG(a, b, c, d, x[1],  5,  0xf61e2562);
    GG(d, a, b, c, x[6],  9,  0xc040b340);
    GG(c, d, a, b, x[11], 14, 0x265e5a51);
    GG(b, c, d, a, x[0],  20, 0xe9b6c7aa);
    GG(a, b, c, d, x[5],  5,  0xd62f105d);
    GG(d, a, b, c, x[10], 9,  0x02441453);
    GG(c, d, a, b, x[15], 14, 0xd8a1e681);
    GG(b, c, d, a, x[4],  20, 0xe7d3fbc8);
    GG(a, b, c, d, x[9],  5,  0x21e1cde6);
    GG(d, a, b, c, x[14], 9,  0xc33707d6);
    GG(c, d, a, b, x[3],  14, 0xf4d50d87);
    GG(b, c, d, a, x[8],  20, 0x455a14ed);
    GG(a, b, c, d, x[13], 5,  0xa9e3e905);
    GG(d, a, b, c, x[2],  9,  0xfcefa3f8);
    GG(c, d, a, b, x[7],  14, 0x676f02d9);
    GG(b, c, d, a, x[12], 20, 0x8d2a4c8a);
    
    // Round 3
    HH(a, b, c, d, x[5],  4,  0xfffa3942);
    HH(d, a, b, c, x[8],  11, 0x8771f681);
    HH(c, d, a, b, x[11], 16, 0x6d9d6122);
    HH(b, c, d, a, x[14], 23, 0xfde5380c);
    HH(a, b, c, d, x[1],  4,  0xa4beea44);
    HH(d, a, b, c, x[4],  11, 0x4bdecfa9);
    HH(c, d, a, b, x[7],  16, 0xf6bb4b60);
    HH(b, c, d, a, x[10], 23, 0xbebfbc70);
    HH(a, b, c, d, x[13], 4,  0x289b7ec6);
    HH(d, a, b, c, x[0],  11, 0xeaa127fa);
    HH(c, d, a, b, x[3],  16, 0xd4ef3085);
    HH(b, c, d, a, x[6],  23, 0x04881d05);
    HH(a, b, c, d, x[9],  4,  0xd9d4d039);
    HH(d, a, b, c, x[12], 11, 0xe6db99e5);
    HH(c, d, a, b, x[15], 16, 0x1fa27cf8);
    HH(b, c, d, a, x[2],  23, 0xc4ac5665);
    
    // Round 4
    II(a, b, c, d, x[0],  6,  0xf4292244);
    II(d, a, b, c, x[7],  10, 0x432aff97);
    II(c, d, a, b, x[14], 15, 0xab9423a7);
    II(b, c, d, a, x[5],  21, 0xfc93a039);
    II(a, b, c, d, x[12], 6,  0x655b59c3);
    II(d, a, b, c, x[3],  10, 0x8f0ccc92);
    II(c, d, a, b, x[10], 15, 0xffeff47d);
    II(b, c, d, a, x[1],  21, 0x85845dd1);
    II(a, b, c, d, x[8],  6,  0x6fa87e4f);
    II(d, a, b, c, x[15], 10, 0xfe2ce6e0);
    II(c, d, a, b, x[6],  15, 0xa3014314);
    II(b, c, d, a, x[13], 21, 0x4e0811a1);
    II(a, b, c, d, x[4],  6,  0xf7537e82);
    II(d, a, b, c, x[11], 10, 0xbd3af235);
    II(c, d, a, b, x[2],  15, 0x2ad7d2bb);
    II(b, c, d, a, x[9],  21, 0xeb86d391);
    
    // Store result
    output[gid * 4] = a + md5_init[0];
    output[gid * 4 + 1] = b + md5_init[1];
    output[gid * 4 + 2] = c + md5_init[2];
    output[gid * 4 + 3] = d + md5_init[3];
}
"""

# Parallel chunk processing kernel for large files
PARALLEL_CHUNK_KERNEL = """
#pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable

__kernel void parallel_hash_chunks(__global const uchar* input,
                                 __global uint* output,
                                 const uint chunk_size,
                                 const uint total_chunks) {
    int gid = get_global_id(0);
    
    if (gid >= total_chunks) return;
    
    // Each work item processes one chunk
    int chunk_offset = gid * chunk_size;
    
    // Compute hash for this chunk
    // This is a simplified version - actual implementation would
    // call the appropriate hash function (SHA256 or MD5)
    
    uint hash = 0;
    for (int i = 0; i < chunk_size && (chunk_offset + i) < get_global_size(0) * chunk_size; i++) {
        hash ^= input[chunk_offset + i];
        hash *= 0x01000193; // FNV-1a constants for simple hash
    }
    
    output[gid] = hash;
}
"""

# GPU memory management utilities
MEMORY_MANAGEMENT_KERNEL = """
__kernel void copy_and_pad(__global const uchar* input,
                          __global uchar* padded_output,
                          const uint input_length,
                          const uint padded_length) {
    int gid = get_global_id(0);
    
    if (gid >= padded_length) return;
    
    if (gid < input_length) {
        padded_output[gid] = input[gid];
    } else if (gid == input_length) {
        padded_output[gid] = 0x80; // Padding bit
    } else {
        padded_output[gid] = 0x00; // Zero padding
    }
}

__kernel void combine_chunk_hashes(__global const uint* chunk_hashes,
                                 __global uint* final_hash,
                                 const uint num_chunks,
                                 const uint hash_size) {
    int gid = get_global_id(0);
    
    if (gid >= hash_size) return;
    
    uint combined = 0;
    for (int i = 0; i < num_chunks; i++) {
        combined ^= chunk_hashes[i * hash_size + gid];
    }
    
    final_hash[gid] = combined;
}
"""