// Reproduce the official 1987 Frank Crow Utah teapot OBJ from the
// University of Utah Graphics Lab generator downloaded beside this script.
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const generatorPath = process.argv[2];
const outputPath = process.argv[3];
if (!generatorPath || !outputPath) {
  throw new Error("usage: node generate_official_teapot.js <teapot_generator.js> <output.obj>");
}

process.chdir(path.dirname(generatorPath));
global.require = require;
global.__dirname = path.dirname(generatorPath);
global.Module = {
  onRuntimeInitialized: () => {
    const c = (name, result, args) => Module.cwrap(name, result, args);
    const generate = c("qmeshx_generate", "", ["number", "number", "number"]);
    const numFacesFn = c("qmeshx_numfaces", "number", []);
    const numPositionsFn = c("qmeshx_numpositions", "number", []);
    const numNormalsFn = c("qmeshx_numnormals", "number", []);
    const numTexCoordsFn = c("qmeshx_numtexcoords", "number", []);
    const facesPtrFn = c("qmeshx_faces", "number", []);
    const positionsPtrFn = c("qmeshx_positions", "number", []);
    const normalsPtrFn = c("qmeshx_normals", "number", []);
    const texCoordsPtrFn = c("qmeshx_texcoords", "number", []);
    const clear = c("qmeshx_clear", "", []);

    // Exact 1987 preset plus the official page's default download settings:
    // round bottom, Blinn scale, injective UVs, welded vertices,
    // triangulated tips, symmetric triangulation, and both sides.
    const commonOptions =
      (3 << 4) | (1 << 8) | (2 << 14) | (1 << 20) |
      (1 << 23) | (1 << 24) | (1 << 26) | (1 << 27);
    const resolution = 24;
    let obj = "# Utah Teapot Model\n";
    obj += "# Version: 1987 - Frank Crow\n";
    obj += "# Source: https://graphics.cs.utah.edu/teapot/\n";
    obj += `# Quad-dominant Mesh Resolution: ${resolution}\n`;

    let positionOffset = 0;
    let normalOffset = 0;
    let texCoordOffset = 0;
    let totalFaces = 0;
    const componentStats = [];
    const components = [
      ["handle", 0],
      ["spout", 1],
      ["lid", 2],
      ["body", 3],
    ];
    for (const [name, componentBit] of components) {
      const options = commonOptions | (1 << componentBit);
      generate(options, resolution, -1);
      const numFaces = numFacesFn();
      const numPositions = numPositionsFn();
      const numNormals = numNormalsFn();
      const numTexCoords = numTexCoordsFn();
      const faces = Array.from(new Int32Array(wasmMemory.buffer, facesPtrFn(), numFaces * 12));
      const positions = Array.from(new Float32Array(wasmMemory.buffer, positionsPtrFn(), numPositions * 3));
      const normals = Array.from(new Float32Array(wasmMemory.buffer, normalsPtrFn(), numNormals * 3));
      const texCoords = Array.from(new Float32Array(wasmMemory.buffer, texCoordsPtrFn(), numTexCoords * 2));

      obj += `\no teapot_${name}\ng teapot_${name}\n`;
      for (let i = 0; i < positions.length; i += 3) {
        obj += `v ${+positions[i].toPrecision(7)} ${+positions[i + 1].toPrecision(7)} ${+positions[i + 2].toPrecision(7)}\n`;
      }
      for (let i = 0; i < normals.length; i += 3) {
        obj += `vn ${+normals[i].toPrecision(7)} ${+normals[i + 1].toPrecision(7)} ${+normals[i + 2].toPrecision(7)}\n`;
      }
      for (let i = 0; i < texCoords.length; i += 2) {
        obj += `vt ${+texCoords[i].toPrecision(7)} ${+texCoords[i + 1].toPrecision(7)}\n`;
      }
      const faceVertex = (i) =>
        ` ${faces[i] + 1 + positionOffset}/${faces[i + 2] + 1 + texCoordOffset}/${faces[i + 1] + 1 + normalOffset}`;
      for (let i = 0; i < faces.length; i += 12) {
        obj += "f" + faceVertex(i);
        if (faces[i + 6] === faces[i + 9]) {
          obj += faceVertex(i + 3) + faceVertex(i + 6);
        } else {
          obj += faceVertex(i + 3) + faceVertex(i + 6) + faceVertex(i + 9);
        }
        obj += "\n";
      }
      componentStats.push({ name, numFaces, numPositions, numNormals, numTexCoords });
      positionOffset += numPositions;
      normalOffset += numNormals;
      texCoordOffset += numTexCoords;
      totalFaces += numFaces;
      clear();
    }
    fs.writeFileSync(outputPath, obj);
    console.log(JSON.stringify({ totalFaces, positionOffset, normalOffset, texCoordOffset, resolution, componentStats }));
  },
};

vm.runInThisContext(fs.readFileSync(generatorPath, "utf8"), { filename: generatorPath });
