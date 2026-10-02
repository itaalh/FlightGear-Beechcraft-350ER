"""Numba rasterizers: UV-space baking and a small perspective renderer for previews."""
import numpy as np
import numba as nb


@nb.njit(cache=True)
def bake_uv(tri_uv_px, tri_pos, tri_nrm, tri_obj, W, H, pos_out, nrm_out, obj_out, cnt_out):
    """Rasterize triangles in UV pixel space. tri_uv_px [N,3,2] pixel coords (x,y) with y down."""
    for t in range(tri_uv_px.shape[0]):
        x0, y0 = tri_uv_px[t, 0, 0], tri_uv_px[t, 0, 1]
        x1, y1 = tri_uv_px[t, 1, 0], tri_uv_px[t, 1, 1]
        x2, y2 = tri_uv_px[t, 2, 0], tri_uv_px[t, 2, 1]
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-9:
            continue
        minx = max(int(np.floor(min(x0, x1, x2))) - 1, 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))) + 1, W - 1)
        miny = max(int(np.floor(min(y0, y1, y2))) - 1, 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))) + 1, H - 1)
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                cx = px + 0.5; cy = py + 0.5
                w0 = ((x1 - cx) * (y2 - cy) - (x2 - cx) * (y1 - cy)) / area
                w1 = ((x2 - cx) * (y0 - cy) - (x0 - cx) * (y2 - cy)) / area
                w2 = 1.0 - w0 - w1
                e = -0.02
                if w0 >= e and w1 >= e and w2 >= e:
                    for k in range(3):
                        pos_out[py, px, k] = w0 * tri_pos[t, 0, k] + w1 * tri_pos[t, 1, k] + w2 * tri_pos[t, 2, k]
                        nrm_out[py, px, k] = tri_nrm[t, k]
                    obj_out[py, px] = tri_obj[t]
                    cnt_out[py, px] += 1


@nb.njit(cache=True)
def render(tri_scr, tri_uv, tri_nrm, tri_tex, textures, tex_sizes, W, H, color_out, depth_out, light, view_dirs, spec_k, ambient):
    """tri_scr [N,3,3]: screen x,y and 1/w (inverse view depth). tri_uv [N,3,2] (u,v in 0..1, v up).
    tri_nrm [N,3,3] per-vertex world normals. tri_tex [N] texture index (-1 = flat grey).
    textures: [T, S, S, 4] float32 (padded to max size S); tex_sizes [T,2].
    view_dirs [N,3,3]: per-vertex direction from vertex to camera (world, normalized)."""
    for t in range(tri_scr.shape[0]):
        x0, y0, iw0 = tri_scr[t, 0, 0], tri_scr[t, 0, 1], tri_scr[t, 0, 2]
        x1, y1, iw1 = tri_scr[t, 1, 0], tri_scr[t, 1, 1], tri_scr[t, 1, 2]
        x2, y2, iw2 = tri_scr[t, 2, 0], tri_scr[t, 2, 1], tri_scr[t, 2, 2]
        if iw0 <= 0 or iw1 <= 0 or iw2 <= 0:
            continue
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
        if minx > maxx or miny > maxy:
            continue
        ti = tri_tex[t]
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                cx = px + 0.5; cy = py + 0.5
                b0 = ((x1 - cx) * (y2 - cy) - (x2 - cx) * (y1 - cy)) / area
                b1 = ((x2 - cx) * (y0 - cy) - (x0 - cx) * (y2 - cy)) / area
                b2 = 1.0 - b0 - b1
                if b0 < 0 or b1 < 0 or b2 < 0:
                    continue
                iw = b0 * iw0 + b1 * iw1 + b2 * iw2
                if iw <= depth_out[py, px]:
                    continue
                depth_out[py, px] = iw
                # perspective-correct weights
                p0 = b0 * iw0 / iw; p1 = b1 * iw1 / iw; p2 = b2 * iw2 / iw
                nx = p0 * tri_nrm[t, 0, 0] + p1 * tri_nrm[t, 1, 0] + p2 * tri_nrm[t, 2, 0]
                ny = p0 * tri_nrm[t, 0, 1] + p1 * tri_nrm[t, 1, 1] + p2 * tri_nrm[t, 2, 1]
                nz = p0 * tri_nrm[t, 0, 2] + p1 * tri_nrm[t, 1, 2] + p2 * tri_nrm[t, 2, 2]
                nl = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-12
                nx /= nl; ny /= nl; nz /= nl
                vx = p0 * view_dirs[t, 0, 0] + p1 * view_dirs[t, 1, 0] + p2 * view_dirs[t, 2, 0]
                vy = p0 * view_dirs[t, 0, 1] + p1 * view_dirs[t, 1, 1] + p2 * view_dirs[t, 2, 1]
                vz = p0 * view_dirs[t, 0, 2] + p1 * view_dirs[t, 1, 2] + p2 * view_dirs[t, 2, 2]
                vl = np.sqrt(vx * vx + vy * vy + vz * vz) + 1e-12
                vx /= vl; vy /= vl; vz /= vl
                # two-sided: flip normal towards viewer
                if nx * vx + ny * vy + nz * vz < 0:
                    nx = -nx; ny = -ny; nz = -nz
                r = 0.10; g = 0.12; b = 0.14
                if ti >= 0:
                    u = p0 * tri_uv[t, 0, 0] + p1 * tri_uv[t, 1, 0] + p2 * tri_uv[t, 2, 0]
                    v = p0 * tri_uv[t, 0, 1] + p1 * tri_uv[t, 1, 1] + p2 * tri_uv[t, 2, 1]
                    u = u - np.floor(u); v = v - np.floor(v)
                    sw = tex_sizes[ti, 0]; sh = tex_sizes[ti, 1]
                    fx = u * sw - 0.5; fy = (1.0 - v) * sh - 0.5
                    ix = int(np.floor(fx)); iy = int(np.floor(fy))
                    ax = fx - ix; ay = fy - iy
                    ix0 = min(max(ix, 0), sw - 1); ix1 = min(max(ix + 1, 0), sw - 1)
                    iy0 = min(max(iy, 0), sh - 1); iy1 = min(max(iy + 1, 0), sh - 1)
                    r = (textures[ti, iy0, ix0, 0] * (1 - ax) + textures[ti, iy0, ix1, 0] * ax) * (1 - ay) + (textures[ti, iy1, ix0, 0] * (1 - ax) + textures[ti, iy1, ix1, 0] * ax) * ay
                    g = (textures[ti, iy0, ix0, 1] * (1 - ax) + textures[ti, iy0, ix1, 1] * ax) * (1 - ay) + (textures[ti, iy1, ix0, 1] * (1 - ax) + textures[ti, iy1, ix1, 1] * ax) * ay
                    b = (textures[ti, iy0, ix0, 2] * (1 - ax) + textures[ti, iy0, ix1, 2] * ax) * (1 - ay) + (textures[ti, iy1, ix0, 2] * (1 - ax) + textures[ti, iy1, ix1, 2] * ax) * ay
                ndl = nx * light[0] + ny * light[1] + nz * light[2]
                if ndl < 0:
                    ndl = 0.0
                # blinn-phong
                hx = light[0] + vx; hy = light[1] + vy; hz = light[2] + vz
                hl = np.sqrt(hx * hx + hy * hy + hz * hz) + 1e-12
                ndh = (nx * hx + ny * hy + nz * hz) / hl
                if ndh < 0:
                    ndh = 0.0
                sp = spec_k * ndh ** 40
                sky = 0.5 + 0.5 * ny  # hemispheric ambient
                amb = ambient * (0.65 + 0.35 * sky)
                lit = amb + (1.0 - ambient) * ndl
                color_out[py, px, 0] = r * lit + sp
                color_out[py, px, 1] = g * lit + sp
                color_out[py, px, 2] = b * lit + sp


@nb.njit(cache=True)
def render_pos(tri_scr, tri_pos, tri_id, W, H, pos_out, id_out, depth_out):
    for t in range(tri_scr.shape[0]):
        x0, y0, iw0 = tri_scr[t, 0, 0], tri_scr[t, 0, 1], tri_scr[t, 0, 2]
        x1, y1, iw1 = tri_scr[t, 1, 0], tri_scr[t, 1, 1], tri_scr[t, 1, 2]
        x2, y2, iw2 = tri_scr[t, 2, 0], tri_scr[t, 2, 1], tri_scr[t, 2, 2]
        if iw0 <= 0 or iw1 <= 0 or iw2 <= 0:
            continue
        area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
        if abs(area) < 1e-12:
            continue
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
        for py in range(miny, maxy + 1):
            for px in range(minx, maxx + 1):
                cx = px + 0.5; cy = py + 0.5
                b0 = ((x1 - cx) * (y2 - cy) - (x2 - cx) * (y1 - cy)) / area
                b1 = ((x2 - cx) * (y0 - cy) - (x0 - cx) * (y2 - cy)) / area
                b2 = 1.0 - b0 - b1
                if b0 < 0 or b1 < 0 or b2 < 0:
                    continue
                iw = b0 * iw0 + b1 * iw1 + b2 * iw2
                if iw <= depth_out[py, px]:
                    continue
                depth_out[py, px] = iw
                p0 = b0 * iw0 / iw; p1 = b1 * iw1 / iw; p2 = b2 * iw2 / iw
                for k in range(3):
                    pos_out[py, px, k] = p0 * tri_pos[t, 0, k] + p1 * tri_pos[t, 1, k] + p2 * tri_pos[t, 2, k]
                id_out[py, px] = tri_id[t]
