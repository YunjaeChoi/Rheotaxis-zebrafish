import * as React from "react";
import * as Immutable from "immutable";
import { connect } from "react-redux";
import { actions, selectors } from "@nteract/core";
import {
  AppState,
  ContentRef,
  KernelRef,
} from "@nteract/types";
import { CellId } from "@nteract/commutable";
import {
  Button,
} from 'semantic-ui-react'
import 'semantic-ui-css/semantic.min.css'

type ButtonProps = ButtonStateProps & ButtonOwnProps;

interface ButtonOwnProps {
  content: string;
  negative: bool;
  fluid: bool;
}

interface ButtonStateProps {
  contentRef: ContentRef;
  kernelRef: KernelRef;
}

class IntButton extends React.Component<ButtonProps> {
  onClick = () => {
    this.props.dispatch(actions.interruptKernel({kernelRef:this.props.kernelRef}))
  }

  render() {
    return (
      <Button
        onClick={this.onClick}
        content={this.props.content}
        negative={this.props.negative}
        fluid={this.props.fluid}
      >
      </Button>
    );
  }
}

const makeMapStateToProps = (
  initialState: AppState,
  { contentRef }: { contentRef: ContentRef }
) => {
  if (!contentRef) {
    throw new Error("<Notebook /> has to have a contentRef");
  }

  const mapStateToProps = (state: AppState, ownProps: ButtonOwnProps): ButtonStateProps => {
    const content = selectors.content(state, { contentRef });
    const model = selectors.model(state, { contentRef });

    if (!model || !content) {
      throw new Error(
        "<Notebook /> has to have content & model that are notebook types"
      );
    }

    if (model.type !== "notebook") {
      return {
        kernelRef: null
      };
    }

    const kernelRef = model.kernelRef

    return {
      kernelRef
    };
  };

  return mapStateToProps;
};

export const InterruptButton = connect(makeMapStateToProps)(IntButton);
