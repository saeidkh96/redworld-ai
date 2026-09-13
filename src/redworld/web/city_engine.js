/* RedWorld Visual City Engine v0.1.21
 * Deterministic procedural city-scene generator.
 * It never changes simulation state; it only creates visual parcels and props
 * around the authoritative geography/road graph.
 */
(function attachRedWorldCityEngine(global) {
  "use strict";

  function hashCode(text) {
    let hash = 2166136261;
    for (let i = 0; i < text.length; i += 1) {
      hash ^= text.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
  }

  function rand(text, min = 0, max = 1) {
    return min + (hashCode(text) / 4294967295) * (max - min);
  }

  function distanceToSegment(px, py, x1, y1, x2, y2) {
    const vx = x2 - x1;
    const vy = y2 - y1;
    const wx = px - x1;
    const wy = py - y1;
    const len2 = vx * vx + vy * vy;
    if (!len2) return Math.hypot(px - x1, py - y1);
    const t = Math.max(0, Math.min(1, (wx * vx + wy * vy) / len2));
    return Math.hypot(px - (x1 + t * vx), py - (y1 + t * vy));
  }

  function nearRoad(snapshot, x, y, clearance) {
    return (snapshot.roads || []).some((road) => (
      distanceToSegment(x, y, road.x1, road.y1, road.x2, road.y2) < clearance
    ));
  }

  function nearLocation(snapshot, x, y, clearance) {
    return (snapshot.locations || []).some((location) => (
      Math.hypot(x - location.x, y - location.y) < clearance
    ));
  }

  function buildingClass(kind, index) {
    if (kind === "residential" || kind === "mixed") return index % 11 === 0 ? "apartment" : "house";
    if (kind === "industrial") return index % 5 === 0 ? "factory" : "warehouse";
    if (kind === "education") return index % 5 === 0 ? "campus" : "academic";
    if (kind === "civic") return index % 6 === 0 ? "civic" : "office";
    if (kind === "commercial") return index % 7 === 0 ? "shop" : "tower";
    if (kind === "central") return index % 9 === 0 ? "plaza" : "tower";
    return "office";
  }

  function dimensions(kind, type, id) {
    if (type === "house") return {
      width: rand(`${id}:w`, .72, 1.15), depth: rand(`${id}:d`, .58, .95), height: rand(`${id}:h`, .62, 1.18),
    };
    if (type === "apartment") return {
      width: rand(`${id}:w`, 1.0, 1.55), depth: rand(`${id}:d`, .78, 1.2), height: rand(`${id}:h`, 1.7, 3.6),
    };
    if (type === "tower") return {
      width: rand(`${id}:w`, .95, 1.55), depth: rand(`${id}:d`, .78, 1.25), height: rand(`${id}:h`, 3.0, kind === "central" ? 7.8 : 6.1),
    };
    if (type === "warehouse" || type === "factory") return {
      width: rand(`${id}:w`, 1.55, 2.7), depth: rand(`${id}:d`, 1.05, 1.9), height: rand(`${id}:h`, .6, 1.45),
    };
    if (type === "campus" || type === "academic") return {
      width: rand(`${id}:w`, 1.25, 2.2), depth: rand(`${id}:d`, .95, 1.65), height: rand(`${id}:h`, 1.2, 3.2),
    };
    if (type === "shop") return {
      width: rand(`${id}:w`, 1.0, 1.8), depth: rand(`${id}:d`, .75, 1.25), height: rand(`${id}:h`, .75, 1.45),
    };
    return {
      width: rand(`${id}:w`, .95, 1.65), depth: rand(`${id}:d`, .72, 1.25), height: rand(`${id}:h`, 1.2, 4.0),
    };
  }

  function districtGrid(snapshot, district) {
    const items = [];
    const dense = district.kind === "central" || district.kind === "commercial";
    const residential = district.kind === "residential" || district.kind === "mixed";
    const industrial = district.kind === "industrial";
    const spacingX = dense ? 1.55 : residential ? 1.45 : industrial ? 2.05 : 1.7;
    const spacingY = dense ? 1.45 : residential ? 1.38 : industrial ? 1.9 : 1.6;
    const minX = district.x - district.width * .43;
    const maxX = district.x + district.width * .43;
    const minY = district.y - district.height * .43;
    const maxY = district.y + district.height * .43;
    let index = 0;

    for (let x = minX; x <= maxX; x += spacingX) {
      for (let y = minY; y <= maxY; y += spacingY) {
        const id = `parcel:${district.id}:${index}`;
        index += 1;
        const jitterX = rand(`${id}:jx`, -.25, .25);
        const jitterY = rand(`${id}:jy`, -.22, .22);
        const px = x + jitterX;
        const py = y + jitterY;
        const clearance = industrial ? 1.15 : dense ? .92 : .82;
        if (nearRoad(snapshot, px, py, clearance)) continue;
        if (nearLocation(snapshot, px, py, clearance * .82)) continue;
        // Intentional empty parcels create readable courtyards and pocket parks.
        if (hashCode(`${id}:skip`) % (dense ? 13 : 9) === 0) {
          items.push({ id, x: px, y: py, type: "pocket-park", districtKind: district.kind });
          continue;
        }
        const type = buildingClass(district.kind, index);
        if (type === "plaza") {
          items.push({ id, x: px, y: py, type: "plaza", districtKind: district.kind });
          continue;
        }
        items.push({
          id,
          x: px,
          y: py,
          type,
          districtKind: district.kind,
          ...dimensions(district.kind, type, id),
          variant: hashCode(id) % 8,
        });
      }
    }
    return items;
  }

  function nearParcel(parcels, x, y, padding = .3) {
    return parcels.some((parcel) => {
      if (["pocket-park", "plaza"].includes(parcel.type)) return false;
      const halfW = (parcel.width || 1) * .58 + padding;
      const halfD = (parcel.depth || 1) * .58 + padding;
      return Math.abs(x - parcel.x) < halfW && Math.abs(y - parcel.y) < halfD;
    });
  }

  function greenSpaces(snapshot, parcels) {
    const zones = [];
    const shrubs = [];
    const flowers = [];
    parcels.filter((parcel) => parcel.type === "pocket-park").forEach((parcel, index) => {
      zones.push({ id: `green-zone:${parcel.id}`, x: parcel.x, y: parcel.y, width: rand(`${parcel.id}:gw`, 1.55, 2.15), depth: rand(`${parcel.id}:gd`, 1.25, 1.8), kind: index % 4 === 0 ? "garden" : "lawn", variant: index % 5 });
      for (let i = 0; i < 5; i += 1) {
        shrubs.push({ id: `shrub:${parcel.id}:${i}`, x: parcel.x + rand(`${parcel.id}:sx:${i}`, -.62, .62), y: parcel.y + rand(`${parcel.id}:sy:${i}`, -.48, .48), size: rand(`${parcel.id}:ss:${i}`, .08, .15), variant: i % 4 });
      }
      if (index % 3 === 0) flowers.push({ id: `flowers:${parcel.id}`, x: parcel.x, y: parcel.y, variant: index % 4 });
    });
    (snapshot.districts || []).forEach((district) => {
      const target = district.kind === "residential" || district.kind === "mixed" ? 10 : 6;
      let accepted = 0;
      for (let i = 0; i < 36 && accepted < target; i += 1) {
        const id = `district-green:${district.id}:${i}`;
        const x = district.x + rand(`${id}:x`, -district.width * .4, district.width * .4);
        const y = district.y + rand(`${id}:y`, -district.height * .4, district.height * .4);
        if (nearRoad(snapshot, x, y, 1.05) || nearLocation(snapshot, x, y, .95) || nearParcel(parcels, x, y, .48)) continue;
        zones.push({ id, x, y, width: rand(`${id}:w`, 1.5, 2.7), depth: rand(`${id}:d`, 1.15, 2.1), kind: accepted % 3 === 0 ? "garden" : "lawn", variant: accepted % 5 });
        accepted += 1;
      }
    });
    return { zones, shrubs, flowers };
  }

  function roadTrees(snapshot) {
    const trees = [];
    (snapshot.roads || []).forEach((road, roadIndex) => {
      if (road.kind === "access") return;
      const dx = road.x2 - road.x1;
      const dy = road.y2 - road.y1;
      const length = Math.hypot(dx, dy);
      if (length < 3) return;
      const nx = -dy / length;
      const ny = dx / length;
      const count = Math.max(1, Math.floor(length / 2.6));
      for (let i = 1; i < count; i += 1) {
        const t = i / count;
        for (const side of [-1, 1]) {
          const offset = road.kind === "arterial" ? 1.75 : 1.25;
          const x = road.x1 + dx * t + nx * offset * side;
          const y = road.y1 + dy * t + ny * offset * side;
          if (nearLocation(snapshot, x, y, .75)) continue;
          trees.push({
            id: `road-tree:${roadIndex}:${i}:${side}`,
            x,
            y,
            size: road.kind === "arterial" ? .31 : .26,
            variant: (roadIndex + i + (side > 0 ? 2 : 0)) % 5,
          });
        }
      }
    });
    return trees;
  }

  function districtTrees(snapshot, parcels) {
    const trees = [];
    (snapshot.districts || []).forEach((district) => {
      const count = district.kind === "residential" || district.kind === "mixed" ? 118 : 76;
      for (let i = 0; i < count; i += 1) {
        const id = `tree:${district.id}:${i}`;
        const x = district.x + rand(`${id}:x`, -district.width * .46, district.width * .46);
        const y = district.y + rand(`${id}:y`, -district.height * .46, district.height * .46);
        if (nearRoad(snapshot, x, y, .72)) continue;
        if (nearLocation(snapshot, x, y, .65)) continue;
        if (nearParcel(parcels, x, y, .22)) continue;
        trees.push({ id, x, y, size: rand(`${id}:s`, .18, .38), variant: i % 5 });
      }
    });
    return trees;
  }

  function streetLamps(snapshot) {
    const lamps = [];
    (snapshot.roads || []).forEach((road, roadIndex) => {
      if (road.kind === "access") return;
      const dx = road.x2 - road.x1;
      const dy = road.y2 - road.y1;
      const length = Math.hypot(dx, dy);
      if (length < 4) return;
      const nx = -dy / length;
      const ny = dx / length;
      const count = Math.max(1, Math.floor(length / 4.4));
      for (let i = 1; i < count; i += 1) {
        const t = i / count;
        const side = i % 2 === 0 ? 1 : -1;
        const offset = road.kind === "arterial" ? 1.25 : .95;
        lamps.push({
          id: `lamp:${roadIndex}:${i}`,
          x: road.x1 + dx * t + nx * offset * side,
          y: road.y1 + dy * t + ny * offset * side,
        });
      }
    });
    return lamps;
  }

  class RedWorldCityEngine {
    constructor() {
      this.scene = null;
      this.key = "";
    }

    build(snapshot) {
      const key = [
        snapshot?.summary?.population || 0,
        snapshot?.districts?.length || 0,
        snapshot?.locations?.length || 0,
        snapshot?.roads?.length || 0,
      ].join(":");
      if (this.scene && this.key === key) return this.scene;
      const parcels = (snapshot.districts || []).flatMap((district) => districtGrid(snapshot, district));
      const greenery = greenSpaces(snapshot, parcels);
      parcels.sort((a, b) => (a.x + a.y) - (b.x + b.y));
      this.scene = {
        parcels,
        greenZones: greenery.zones,
        shrubs: greenery.shrubs,
        flowers: greenery.flowers,
        trees: [...districtTrees(snapshot, parcels), ...roadTrees(snapshot)],
        lamps: streetLamps(snapshot),
      };
      this.key = key;
      return this.scene;
    }

    invalidate() {
      this.scene = null;
      this.key = "";
    }
  }

  global.RedWorldCityEngine = RedWorldCityEngine;
}(window));
