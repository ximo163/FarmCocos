import {
    Node, director, Director, Canvas, Camera, Layers, UITransform, Graphics, Color, view,
    ResolutionPolicy, resources, SpriteFrame, Sprite,
} from 'cc';
import { CORE_API_VERSION } from './shared/core/version';

// 啟動腳本：main.scene 是空場景，Canvas、相機和所有界面都在運行時由代碼建立。
// 這個文件只做兩件事：搭好 Canvas，並給自動化測試留一個掛鉤 globalThis.__farm。
// 遊戲界面以後由 packages/ 裡的佈局邏輯按 layouts/*.json 生成，接在 Root 節點下。

const DESIGN_W = 960;
const DESIGN_H = 640;
const UI = Layers.Enum.UI_2D;

interface FarmHook {
    ready: boolean;
    coreApi: number;
    // 'pending' | 'ok' | 'failed: <原因>'：resources 下沒有提交 .meta 的圖片能不能加載
    probe: string;
}

const hook: FarmHook = { ready: false, coreApi: CORE_API_VERSION, probe: 'pending' };
(globalThis as unknown as { __farm: FarmHook }).__farm = hook;

function bootstrap() {
    const scene = director.getScene();
    if (!scene || scene.getChildByName('Canvas')) return;

    view.setDesignResolutionSize(DESIGN_W, DESIGN_H, ResolutionPolicy.SHOW_ALL);

    const canvasNode = new Node('Canvas');
    canvasNode.layer = UI;
    scene.addChild(canvasNode);
    canvasNode.addComponent(UITransform).setContentSize(DESIGN_W, DESIGN_H);

    const camNode = new Node('Camera');
    camNode.layer = UI;
    canvasNode.addChild(camNode);
    camNode.setPosition(0, 0, 1000);
    const cam = camNode.addComponent(Camera);
    cam.projection = Camera.ProjectionType.ORTHO;
    cam.visibility = UI;
    cam.clearFlags = Camera.ClearFlag.SOLID_COLOR;
    cam.clearColor = new Color(20, 24, 40, 255);
    cam.near = 1;
    cam.far = 2000;
    cam.orthoHeight = DESIGN_H / 2;

    const canvas = canvasNode.addComponent(Canvas);
    canvas.cameraComponent = cam;
    canvas.alignCanvasWithScreen = true;

    const root = new Node('Root');
    root.layer = UI;
    canvasNode.addChild(root);
    root.addComponent(UITransform).setContentSize(DESIGN_W, DESIGN_H);

    // 啟動標記：屏幕正中一塊固定顏色的方塊，冒煙測試靠它確認畫面真的渲染出來了。
    const g = root.addComponent(Graphics);
    g.fillColor = new Color(16, 192, 64, 255);
    g.rect(-150, -150, 300, 300);
    g.fill();

    resources.load('probe/spriteFrame', SpriteFrame, (err, frame) => {
        if (err || !frame) {
            hook.probe = 'failed: ' + (err ? err.message : 'empty');
            return;
        }
        const n = new Node('Probe');
        n.layer = UI;
        root.addChild(n);
        n.setPosition(-DESIGN_W / 2 + 60, DESIGN_H / 2 - 60, 0);
        n.addComponent(UITransform).setContentSize(64, 64);
        const sp = n.addComponent(Sprite);
        sp.sizeMode = Sprite.SizeMode.CUSTOM;
        sp.spriteFrame = frame;
        hook.probe = 'ok';
    });

    director.once(Director.EVENT_AFTER_DRAW, () => { hook.ready = true; });
}

director.on(Director.EVENT_AFTER_SCENE_LAUNCH, bootstrap);
